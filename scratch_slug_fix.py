from dataset.models import Dataset
from django.utils.text import slugify

datasets = Dataset.objects.filter(slug__isnull=True) | Dataset.objects.filter(slug='')
count = 0
for d in datasets:
    d.slug = slugify(d.title) + '-' + str(d.id)
    d.save(update_fields=['slug'])
    count += 1
print(f'Updated {count} datasets without slugs.')
