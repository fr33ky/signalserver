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
from .forms import UploadFileForm
from .models import Video
from .models import Result
from .models import Row
from groups.models import Group
from groups.models import Member
from .forms import VideoForm
from .forms import ConfigForm
from .forms import GroupForm
from .processfiles import process_file_original
from .processfiles import delete_file
from .processfiles import process_file_with_config
from .processfiles import get_full_path_file_name
from celery import group
from .tasks import add
from .tasks import process_bulk
from .tasks import process_file
from celery.result import AsyncResult
from operations.models import Configuration
from operations.models import Operation
from django.http import JsonResponse
from django.db import IntegrityError


def index(request):
    ce = add.delay(1, 1)
    status = ce.ready()
    if status:
        st = "hello" + str(ce.get())
    else:
        st = "not ready"
    return HttpResponse(
        "Hello, world. You're at the file upload index. %s" % st)


def detail(request, question_id):
    return HttpResponse("You're looking at question %s." % filename_id)


def results(request, question_id):
    response = "You're looking at the results of question %s."
    return HttpResponse(response % filename_id)


def show_result(request, video_videofile_name):
    video_videofile_name = get_full_path_file_name(video_videofile_name)
    newst = process_file_original(video_videofile_name)
    return HttpResponse("Hello, world, index. {0}".format(newst))


def show_video(request, video_videofile_name):
    video = Video.objects.get(filename=video_videofile_name)
    form = ConfigForm()
    return render(request, 'fileuploads/show.html',
                  {'video': video, 'form': form})


def delete_video(request, video_videofile_name):
    delete_file(video_videofile_name)
    return HttpResponseRedirect(reverse('fileuploads:list'))


def get_filename(original_name):
    if original_name.endswith('.gz'):
        original_name = os.path.splitext(original_name)[0]
    name = os.path.splitext(original_name)[0]
    return name


def process(request):
    if request.method == 'POST':
        original_file_name = request.POST['file_name']
        config_id = request.POST['config_fields']
        file_name = get_full_path_file_name(original_file_name)
        result = process_file_with_config(
            file_name, config_id, original_file_name)
        return render(request, 'fileuploads/process.html',
                      {'result': result})


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


def bulk_process(request):
    if request.method == 'POST':
        videos = Video.objects.all()
        config_id = request.POST['config_fields']
        config_name = Configuration.objects.get(
            id=config_id).configuration_name
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_time = datetime.strptime(current_time_str,
                                         "%Y-%m-%d %H:%M:%S")
        for v in videos:
            file_process(v.filename, config_id, config_name,
                         current_time_str, current_time)
    return HttpResponseRedirect("../status")


def search_result(start_field, end_field, keyword):
    start = datetime.strptime(start_field,
                              "%Y/%m/%d %H:%M")
    end = datetime.strptime(end_field,
                            "%Y/%m/%d %H:%M")
    results = Video.objects.filter(upload_time__range=[start, end])
    if keyword is not None:
        results = results.filter(filename__contains=keyword)
    return results


def search(request):
    files = Video.objects.all()
    if request.method == 'POST':
        start_field = request.POST['start_field']
        end_field = request.POST['end_field']
        keyword = request.POST['keyword']
        videos = search_result(start_field, end_field, keyword)
        form = GroupForm()
        return render(request, 'fileuploads/search.html',
                      {'videos': videos, 'form': form, 'start': start_field,
                       'end': end_field, 'keyword': keyword, 'files': files})

    return render(request, 'fileuploads/search.html',
                  {'files': files})


def status(request):
    results = Result.objects.all()
    for result in results:
        task_id = result.task_id
        work_status = AsyncResult(task_id).ready()
        result.status = work_status
        result.save()

    results = Result.objects.all()
        #
        #    results = group(process_file.s(i, config_id, j)
        #                    for i, j in zip(file_names,
        #
        #task_id = status.task_id

        #status = AsyncResult(task_id).ready()
        #if status:
        #    results = "yay it is done"
        #else:
        #    results = "still working on it"

            #results.append(result)

    return render(request, 'fileuploads/status.html',
                  {'results': results})


def upload(request):
    # Handle file upload
    form = VideoForm()
    if request.method == 'POST':

        form = VideoForm(request.POST, request.FILES)
        files = request.FILES.getlist('videofile')
        #original_name = request.FILES['videofile'].name
        #name = get_filename(original_name)

        #count = Video.objects.filter(filename=name).count()
        #num = 1
        #while item > 0:
        #    name = name + '(' + str(num) + ')'
        #    item = Video.objects.filter(filename=name).count()
        #    num += 1
        if form.is_valid():
            for f in files:
                original_name = f.name
                name = get_filename(original_name)
                count = Video.objects.filter(filename=name).count()
                if count > 0:
                    Video.objects.get(filename=name).delete()
                newvideo = Video(
                    videofile=f,
                    filename=name,
                )
                newvideo.save()
            #videos = Video.objects.all()
            #return HttpResponseRedirect(reverse('fileuploads:list',
            #                            kwargs={
            #                                'videos': videos,
            #                                'form': form
            #                                    }))
     #       return HttpResponseRedirect(
     #           reverse('fileuploads:list'))

    # Load documents for the list page
    videos = Video.objects.all()

    # Render list page with the documents and the form
    return render(request, 'fileuploads/list.html',
                  {'videos': videos, 'form': form})


def list(request):
    # Handle file upload
    form = VideoForm()
    videos = Video.objects.all()
    if request.method == 'POST':
        start_field = request.POST['start_field']
        end_field = request.POST['end_field']
        keyword = request.POST['keyword']
        files = search_result(start_field, end_field, keyword)
        return render(request, 'fileuploads/list.html',
                      {'videos': videos, 'form': form, 'start': start_field,
                       'end': end_field, 'keyword': keyword, 'files': files})

    # Render list page with the documents and the form
    return render(request, 'fileuploads/list.html',
                  {'videos': videos, 'form': form})
