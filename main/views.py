import json
import grequests
import requests
import time

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import render, render_to_response, redirect
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.template import RequestContext

from main.models import Story, Organization
from main.utils import post_stories

# TODO:
# -add better/another demo image
# -better phrase pattern matching


def home(request):
    return render_to_response("main/home.html",
                              {'oauth_redirect_uri': request.build_absolute_uri('oauth')},
                              context_instance=RequestContext(request))


# TODO: maybe change this webhook_url_end to a time-generated hash so its more secure?
def change_settings(request, webhook_url_end):
    webhook_url = "https://hooks.slack.com/services/" + webhook_url_end
    org = Organization.objects.get(webhook_url=webhook_url)

    request.session['webhook_url'] = webhook_url
    return render_to_response("main/change_settings.html",
                              {
                                  'posting_settings': org,
                              },
                              context_instance=RequestContext(request))


def oauth(request):
    if request.method != "GET" or 'code' not in request.GET:
        return HttpResponseBadRequest("Oauth failed! No code given.")

    access_params = {
        'client_id': settings.SLACK_CLIENT_ID,
        'client_secret': settings.SLACK_CLIENT_SECRET,
        'code': request.GET['code'],
        'redirect_uri': request.build_absolute_uri('oauth'),  # This must match one provided in the slack app's config
    }

    resp = requests.get("https://slack.com/api/oauth.access", params=access_params)

    if not resp.ok or not resp.json()['ok']:
        return HttpResponseBadRequest("Found code, but could not get access token: " + str(resp.json()))

    webhook_url = resp.json().get('incoming_webhook').get('url')
    access_token = resp.json().get('access_token')

    organization = Organization(webhook_url=webhook_url, access_token=access_token)
    organization.team_name = resp.json()['team_name']
    organization.channel_name = resp.json()['incoming_webhook']['channel']
    organization.config_url = resp.json()['incoming_webhook']['configuration_url']
    organization.save()

    return redirect('change_settings', webhook_url_end=organization.webhook_url_end)


def save_settings(request):
    if request.method != "POST":
        return HttpResponseBadRequest("Not a POST request!")

    if 'webhook_url' not in request.session:
        return HttpResponseBadRequest("No organization is signed in!")

    posting_settings = Organization.objects.get(webhook_url=request.session['webhook_url'])

    # We want to know if this is the first time the org is using SN
    just_created = len(posting_settings.phrases) == 0

    # Collect all the new phrases sent in the request
    new_phrases = []
    for phrase in json.loads(request.POST['phrases']):
        if phrase.strip() != "":
            new_phrases.append(phrase)

    posting_settings.phrases = new_phrases
    posting_settings.save()

    # If they change keywords or start using SN, we want to post their relevant stories
    recent_stories = Story.objects.values_list('story_id', flat=True).order_by('-story_id')[:500]
    post_stories(recent_stories, posting_settings)

    # Now post the link to change settings if this is the first time
    if just_created:
        settings_link = request.build_absolute_uri(reverse('change_settings', args=[posting_settings.webhook_url_end]))
        resp = requests.post(posting_settings.webhook_url, data=json.dumps(
            {'text': "_<{0}|You can change your article keywords here.>_".format(settings_link)}))

    return HttpResponse("Saved!")


@transaction.atomic
def get_stories(request, offset):
    # We do this stupid offset thing because web requests to heroku timeout after 30s...
    # So essentially we just hit /getstories 5 times, grabbing 100 stories each time
    offset = int(offset) * 100
    top_stories = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json").json()[offset: offset + 100]

    start_time = time.time()

    # Figure out which stories we don't have saved in our database yet
    new_story_ids = []
    for story_id in top_stories:
        if not Story.objects.filter(story_id=story_id).exists():
            new_story_ids.append(story_id)

    # The fun part: asynchronously hit HN api for all the info we need using grequests
    # This is ~5x faster than synchronous requests for big updates
    urls = ["https://hacker-news.firebaseio.com/v0/item/{0}.json".format(story_id) for story_id in new_story_ids]
    new_rs = (grequests.get(u, timeout=10) for u in urls)
    new_resps = grequests.map(new_rs)

    # Store all of our new stories in the database
    for resp in new_resps:
        Story.create_from_story_resp(resp)

    # Go through every organization and figure out which stories they haven't seen yet
    for posting_settings in Organization.objects.filter(uninstalled=False):
        posted = post_stories(top_stories, posting_settings)

        if posted and offset == 400:
            settings_link = request.build_absolute_uri(reverse('change_settings', args=[posting_settings.webhook_url_end]))

            resp = requests.post(posting_settings.webhook_url, data=json.dumps(
                {'text': "_<{0}|You can change your article keywords here.>_".format(settings_link)}))

    return HttpResponse("Found new stories in {0} seconds!".format(str(time.time() - start_time)))
