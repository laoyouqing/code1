# Generated by Django 2.1.1 on 2019-07-15 02:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('goods', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='goods',
            name='activity',
            field=models.CharField(max_length=200, verbose_name='活动规则'),
        ),
        migrations.AlterField(
            model_name='goods',
            name='activity_rules',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='goods.Activity', verbose_name='活动'),
        ),
        migrations.AlterField(
            model_name='ordergoods',
            name='status',
            field=models.SmallIntegerField(choices=[(0, '砍价中'), (1, '已完成'), (2, '已结束'), (3, '已支付'), (4, '已核销')], default=0, verbose_name='状态'),
        ),
    ]
