import json
import requests

from main.models import Story


def post_stories(story_ids, posting_settings):
    key_phrases = set(posting_settings.phrases)

    already_posted = set(posting_settings.posted_stories)
    relevant_stories = []
    for story_id in story_ids:
        if story_id in already_posted:
            continue  # don't post a story more than once

        story = Story.objects.get(story_id=story_id)
        for phrase in key_phrases:
            if phrase.lower() in story.name.lower():
                relevant_stories.append([story, phrase])
                already_posted.add(story_id)
                break

    # Update the org's list of already posted stories
    posting_settings.posted_stories = list(already_posted)
    posting_settings.save()

    for [story, phrase] in relevant_stories:
        resp = requests.post(posting_settings.webhook_url, data=json.dumps({'text': story.post_text(phrase),
                                                                            }))

    return len(relevant_stories) != 0
