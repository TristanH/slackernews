import json
import requests

from django.contrib.auth.models import User
from django.db import models


class Story(models.Model):

    def __unicode__(self):
        return self.name

    story_id = models.PositiveIntegerField(blank=False, null=False, db_index=True, unique=True)

    num_comments = models.PositiveIntegerField(null=False, blank=False)

    name = models.CharField(max_length=511, null=False, blank=False)

    @staticmethod
    def create_from_story_resp(resp):
        if not resp.ok:
            raise Exception("Hitting HN API to get story failed: {0}".format(resp.text))

        story = Story(story_id=resp.json()['id'])
        story.name = resp.json()['title']
        story.num_comments = resp.json().get('descendants', 0)
        story.save()
        return story

    def post_text(self, contains_phrase):
        article_link = "https://news.ycombinator.com/item?id={0}".format(self.story_id)
        return u'New story mentioning "{0}": <{2}|{3}> ({1} comments)'.format(contains_phrase, self.num_comments, article_link, self.name)


class Organization(models.Model):

    # hackily store lists of story ids as a json string.... we have a 10k row limit
    posted_stories_raw = models.TextField(default=json.dumps({}))

    # hackily store lists of phrases as json strings
    phrases_raw = models.TextField(default=json.dumps({}))

    webhook_url = models.CharField(max_length=256, null=False, blank=False, unique=True)

    # Token is not unique because SN can post in multiple channels of one slack team
    access_token = models.CharField(max_length=256, unique=False)

    team_name = models.CharField(max_length=256, unique=False)

    channel_name = models.CharField(max_length=256, unique=False)

    config_url = models.CharField(max_length=256,  unique=False)

    uninstalled = models.BooleanField(default=False)

    @property
    def webhook_url_end(self):
        return self.webhook_url[self.webhook_url.find("hooks.slack.com/services/") + 25:]

    @property
    def posted_stories(self):
        return json.loads(self.posted_stories_raw)

    @posted_stories.setter
    def posted_stories(self, value):
        self.posted_stories_raw = json.dumps(value)

    @property
    def phrases(self):
        return json.loads(self.phrases_raw)

    @phrases.setter
    def phrases(self, value):
        self.phrases_raw = json.dumps(value)
