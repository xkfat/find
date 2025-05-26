from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('location_sharing', '0003_rename_selectedfriends_selectedfriend_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='SelectedFriend',
        ),
        
        migrations.RemoveField(
            model_name='userlocation',
            name='share_with_all_friends',
        ),
        
        migrations.AddField(
            model_name='locationsharing',
            name='can_see_me',
            field=models.BooleanField(default=True),
        ),
    ]