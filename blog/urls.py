"""blog URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf.urls import include
from django.conf.urls import url
from django.conf import settings
from django.conf.urls.static import static
from aweiblog.feed import LatestEntriesFeed
from aweiblog import views as blog_views
from django.contrib.sitemaps import GenericSitemap
from django.contrib.sitemaps.views import sitemap
from aweiblog.models import Entry

info_dict = {
    'queryset': Entry.objects.all(),
    'date_field': 'modified_time'
}


urlpatterns = [
    url(r'^$', blog_views.index),
    url(r'^admin/', admin.site.urls),
    url(r'^blog/', include('aweiblog.urls')),
    url(r'^login/$', blog_views.login),
    url(r'^logout/$', blog_views.logout),
    url(r'^latest/feed/$', LatestEntriesFeed()),
    url(r'^comments/', include('django_comments.urls')),
    url(r'^sitemap\.xml$', sitemap, {'sitemaps': {'blog': GenericSitemap(info_dict, priority=0.6)}},
        name='django.contrib.sitemaps.views.sitemap'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler403 = blog_views.permission_denied
handler404 = blog_views.page_not_found
handler500 = blog_views.page_error
