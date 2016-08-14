import os
from datetime import datetime
import pytz
import json
from django.http import HttpResponse
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.template import loader
from django.views import generic
from django.utils import timezone
from fileuploads.models import Video
from fileuploads.models import Result
from fileuploads.models import Row
from .models import Group
from .models import Member
from fileuploads.forms import ConfigForm
from fileuploads.processfiles import delete_file
from fileuploads.processfiles import get_full_path_file_name
from fileuploads.views import search_result
from celery import group
from fileuploads.tasks import process_file
from celery.result import AsyncResult
from operations.models import Configuration
from operations.models import Operation
from django.http import JsonResponse
from django.db import IntegrityError

# Create your views here.


def save_group(request):
    if request.method == 'POST':
        group_name = request.POST['group_name']
        if " " in group_name:
            group_name = group_name.replace(' ', '-')
        count = Group.objects.filter(group_name=group_name).count()
        if count > 0:
            form = GroupForm()
            message = "the name " + group_name +  \
                      " is taken, please select differnt name"
            start_field = request.POST['start']
            end_field = request.POST['end']
            videos = search_result(start_field, end_field)
            return render(request, 'groups/search.html',
                          {'videos': videos, 'form': form,
                           'start': start_field,
                           'end': end_field,
                           'message': message
                           })
        else:
            new_group = Group(
                group_name=group_name
            )
            new_group.save()
            group = Group.objects.get(group_name=group_name)
            #length of request you don't need group_name, token, start and end
            number = len(request.POST) - 4
            counter = 1
            newkey = "file" + str(counter)
            while counter < number:
                if newkey in request.POST:
                    file_name = request.POST[newkey]
                    save_member(group, file_name)
                counter += 1
                newkey = newkey = "file" + str(counter)
            groups = Group.objects.all()
            form = ConfigForm()
            return render(request, 'groups/group.html',
                          {'groups': groups, 'group': group, 'form': form})
    else:
        groups = Group.objects.all()
        form = ConfigForm()
        return render(request, 'groups/group.html',
                      {'groups': groups, 'form': form})


def edit_group(request, group_name):
    group = Group.objects.get(group_name=group_name)
    files = Video.objects.all()
    if request.method == 'POST':
        start_field = request.POST['start_field']
        end_field = request.POST['end_field']
        keyword = request.POST['keyword']
        videos = search_result(start_field, end_field, keyword)[:50]
        return render(request, 'groups/group_edit.html',
                      {'videos': videos, 'start': start_field, 'group': group,
                       'end': end_field, 'keyword': keyword, 'files': files})

    return render(request, 'groups/group_edit.html',
                  {'group': group, 'files': files})


def search_group(request):
    result_groups = []
    group_name = ''
    if request.method == 'POST':
        group_name = request.POST['group_name']
        result_groups = Group.objects.filter(group_name__contains=group_name)
    groups = Group.objects.all()
    form = ConfigForm()
    return render(request, 'groups/group.html',
                  {'groups': groups,
                   'result_groups': result_groups,
                   'form': form,
                   'keyword': group_name})


def group_process(request):
    if request.method == 'POST':
        group_name = request.POST['group_name']
        group = Group.objects.get(group_name=group_name)
        members = Member.objects.filter(group=group)
        config_id = request.POST['config_fields']
        config_name = Configuration.objects.get(
            id=config_id).configuration_name
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_time = datetime.strptime(current_time_str,
                                         "%Y-%m-%d %H:%M:%S")
        for member in members:
            file_process(member.file_name, config_id, config_name,
                         current_time_str, current_time, group_name)

    groups = Group.objects.all()
    group_results = {}
    for group in groups:
        members = Member.objects.filter(group=group)
        for member in members:
            temp = Result.objects.filter(group_name=group.group_name)
            results = temp.filter(filename=member.file_name)
            update_results(results)
            for result in results:
                pro_time = result.processed_time.strftime("%Y-%m-%d %H:%M:%S")
                key = result.group_name + "-" + pro_time
                if key in group_results:
                    entry = group_results[key]
                    entry.append(result)
                    group_results[key] = entry
                else:
                    group_results[key] = [result]

    not_completed = []
    for key, values in group_results.items():
        for value in values:
            if not value.status:
                not_completed.append(key)

    return render(request, 'groups/group_process.html',
                  {'group_results': group_results,
                   'not_completed': not_completed})


def file_process(file_name, config_id, config_name, current_time_str,
                 current_time, group_name=None):
    original_name = file_name
    file_name = get_full_path_file_name(original_name)
    status = process_file.delay(file_name, config_id,
                                original_name, current_time_str)
    result = Result(
        filename=original_name,
        config_id=config_id,
        config_name=config_name,
        processed_time=current_time,
        task_id=status.task_id,
        status=AsyncResult(status.task_id).ready(),
        group_name=group_name)
    result.save()


def update_results(results):
    for result in results:
        if not result.status:
            task_id = result.task_id
            work_status = AsyncResult(task_id).ready()
            result.status = work_status
            result.save()


def save_member(group, file_name):
    video = Video.objects.get(filename=file_name)
    try:
        new_member = Member(
            file_name=file_name,
            group=group,
            upload_time=video.upload_time,
            file_id=video.id
        )
        new_member.save()
    except IntegrityError:
        pass  # it didn't need to save the dubplicate files


def update_group(request):
    files = Video.objects.all()
    group = ''
    if request.method == 'POST':
        file_names = []
        for key, value in request.POST.items():
            if key == 'group_name':
                group_name = value
                group = Group.objects.get(group_name=group_name)
            elif "file_name" in key:
                file_names.append(value)

        for file_name in file_names:
            save_member(group, file_name)

    return render(request, 'groups/group_edit.html',
                  {'group': group, 'files': files})


def remove_file(request, group_name, file_name):
    group_name = group_name
    group = Group.objects.get(group_name=group_name)
    members = Member.objects.filter(group=group)
    member = members.filter(file_name=file_name)
    member.delete()
    files = Video.objects.all()
    return HttpResponseRedirect(reverse('groups:edit_group',
                                        args=(group_name,)))


def group_result(request):
    groups = Group.objects.all()
    group_results = {}
    for group in groups:
        members = Member.objects.filter(group=group)
        for member in members:
            temp = Result.objects.filter(group_name=group.group_name)
            results = temp.filter(filename=member.file_name)
            for result in results:
                pro_time = result.processed_time.strftime("%Y-%m-%d %H:%M:%S")
                key = result.group_name + "-" + pro_time
                if key in group_results:
                    entry = group_results[key]
                    entry.append(result)
                    group_results[key] = entry
                else:
                    group_results[key] = [result]

    return render(request, 'groups/group_result.html',
                  {'group_results': group_results})


def result_graph(request):
    signal_names = []
    op_names = []
    values = []
    group_name = ''
    processed_time = ''
    config_name = ''
    results = []
    operations = []
    if request.method == 'POST':
        group_name = request.POST['group_name']
        processed_time = request.POST['processed_time']

        processed_time_object = datetime.strptime(processed_time,
                                                  "%Y-%m-%d %H:%M:%S")
        processed_time_object = processed_time_object.replace(tzinfo=pytz.UTC)

        temp = Result.objects.filter(group_name=group_name)
        results = temp.filter(processed_time=processed_time_object)

        for result in results:
            config_name = result.config_name
            configuration = Configuration.objects.filter(
                configuration_name=config_name)
            operations = Operation.objects.filter(
                configuration=configuration).order_by('display_order')
            for operation in operations:
                op_names.append(operation.op_name)
                signal_name = operation.signal_name
                if operation.op_name == 'exceeds':
                    temprows = Row.objects.filter(result=result)
                    rows = temprows.filter(op_name='exceeded')
                if operation.op_name == 'average_difference':
                    signal_name = operation.signal_name + "-" +  \
                        operation.second_signal_name
                signal_names.append(signal_name)

    return render(request, 'groups/result_graph.html',
                  {'group_name': group_name,
                   'processed_time': processed_time,
                   'signal_names': signal_names,
                   'config_name': config_name,
                   'operations': operations,
                   'op_names': op_names
                   })


def show_graphs(request):
    return HttpResponse("You're looking at question")


def get_graph_data(request):
    group_name = request.GET['group_name']
    processed_time = request.GET['processed_time']
    signal_name = request.GET['signal_name']
    op_name = request.GET['op_name']

    data = []

    processed_time_object = datetime.strptime(processed_time,
                                              "%Y-%m-%d %H:%M:%S")
    processed_time_object = processed_time_object.replace(tzinfo=pytz.UTC)

    temp = Result.objects.filter(group_name=group_name)
    results = temp.filter(processed_time=processed_time_object)

    for result in results:
        temprows = Row.objects.filter(result=result)
        sigrows = temprows.filter(signal_name=signal_name)
        if op_name == 'exceeds':
            rows = sigrows.filter(op_name='exceeded')
        else:
            rows = sigrows.filter(op_name=op_name)

        for row in rows:
            if op_name == 'exceeds':
                percent = (row.result_number / row.frame_number) * 100
                signal_data = {
                    "filename": result.filename,
                    "average": percent
                }
            else:
                signal_data = {
                    "filename": result.filename,
                    "average": row.result_number
                }
            data.append(signal_data)
    return JsonResponse(data, safe=False)
