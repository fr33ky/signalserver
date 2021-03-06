from django.conf.urls import url, include

from . import views

app_name = 'fileuploads'
urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^(?P<filename_id>[0-9]+)/$', views.detail, name='detail'),
    url(r'^(?P<filename_id>[0-9]+)/results/$', views.results, name='results'),
    url(r'^about/$', views.about, name='about'),
    url(r'^api/check_progress/$',
        views.check_progress, name='check_progress'),
    url(r'^bulk_delete_files/$', views.bulk_delete_files,
        name='bulk_delete_files'),
    url(r'^check_exist/(?P<filename>[^/]+)$', views.FileUploadView.as_view()),
    url(r'^create_group/$', views.create_new_group_in_file_list,
        name='create_group'),
    url(r'^delete-video/(?P<video_videofile_name>[\w.]{0,256})$',
        views.delete_video, name='delete_video'),
    url(r'^delete_file/$', views.FileDeleteView.as_view()),
    url(r'^download/(?P<file_name>[^/]+)$', views.download, name='download'),
    url(r'^find_files/$', views.find_files, name='find_files'),
    url(r'^list/$', views.list_file, name='list'),
    url(r'^list/show/(?P<file_name>[\w.]{0,256})$',
        views.show_video, name='show_video'),
    url(r'^list/show/result/(?P<video_videofile_name>[\w.]{0,256})$',
        views.show_result, name='show_result'),
    url(r'^process/$', views.process, name='process'),
    url(r'^search/$', views.search, name='search'),
    url(r'^show/(?P<file_name>[\w.]{0,256})$',
        views.show_video, name='show_video'),
    url(r'^status/$', views.status, name='status'),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^upload/(?P<filename>[^/]+)$', views.FileUploadView.as_view()),
]
