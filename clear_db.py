from main.models import Story

up_to_id = Story.objects.all().order_by('id')[5000].id

Story.objects.filter(pk__lt=up_to_id).delete()