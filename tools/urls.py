from django.conf.urls import url
from views import *

urlpatterns = [
    url(r'^$', ToolListView.as_view(), name='tools'),
    url(r'^tool/(?P<pk>[\w-]+)/form$', tool_exec_view, name="tool_form"),

    url(r'^tool/(?P<pk>[\w-]+)$', ToolDetailView.as_view(), name="tool_detail"),
    url(r'^tool/(?P<pk>[\w-]+)/json$', ToolJSONView.as_view(), name="tool_detail_json"),

]