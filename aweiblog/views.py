from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from . import models
from django_comments.models import Comment
import markdown
import pygments
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
from django.db.models import Q
from django_comments import models as comment_models
# Create your views here.

def make_paginator(objects, page, num=5):
    paginator = Paginator(objects, num)
    try:
        object_list = paginator.page(page)
    except PageNotAnInteger:
        object_list = paginator.page(1)
    except EmptyPage:
        object_list = paginator.page(paginator.num_pages)
    return object_list, paginator

def pagination_data(paginator, page):
    if paginator.num_pages ==1:
        return {}
    left = []
    right = []
    left_has_more = False
    right_has_more = False
    first = False
    last = False
    try:
        page_number = int(page)
    except ValueError:
        page_number = 1
    except:
        page_number = 1

    total_pages = paginator.num_pages
    page_range = paginator.page_range

    if page_number == 1:
        right = page_range[page_number:page_number+4]
        if right[-1] < total_pages - 1:
            right_has_more = True
        if right[-1] < total_pages:
            last = True
    elif page_number ==total_pages:
        left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number-1]

        if left[0] > 2:
            left_has_more = True
        if left[0] > 1:
            first = True
    else:
        left = page_range[(page_number - 3) if (page_number - 3) > 0 else 0:page_number-1]
        right = page_range[page_number:page_number + 2]

        if right[-1] < total_pages - 1:
            right_has_more = True
        if right[-1] < total_pages:
            last = True
        if left[0] > 2:
            left_has_more = True
        if left[0] > 1:
            first = True

    data = {
        'left': left,
        'right': right,
        'left_has_more': left_has_more,
        'right_has_more': right_has_more,
        'first': first,
        'last': last,
    }
    return data

def index(request):
    entries = models.Entry.objects.all()
    page = request.GET.get('page', 1)
    entry_list, paginator = make_paginator(entries, page)
    page_data = pagination_data(paginator, page)

    return render(request, 'blog/index.html', locals())

def detail(request, blog_id):
    # entry = models.Entry.objects.get(id=blog_id)
    entry = get_object_or_404(models.Entry, id=blog_id)
    md = markdown.Markdown(extensions=[
      'markdown.extensions.extra',
      'markdown.extensions.codehilite',
      'markdown.extensions.toc',
    ])
    entry.body = md.convert(entry.body)
    entry.toc = md.toc
    entry.increase_visiting()

    comment_list = list()

    def get_comment_list(comments):
        for comment in comments:
            comment_list.append(comment)
            children = comment.child_comment.all()
            if len(children) > 0:
                get_comment_list(children)
    top_comments = Comment.objects.filter(object_pk=blog_id, parent_comment=None,
                                          content_type__app_label='aweiblog').order_by('-submit_date')

    get_comment_list(top_comments)

    return render(request, 'blog/detail.html', locals())

def category(request, category_id):
    # c = models.Category.objects.get(id=category_id)
    c = get_object_or_404(models.Category, id=category_id)
    entries = models.Entry.objects.filter(category=c)
    page = request.GET.get('page', 1)
    entry_list, paginator = make_paginator(entries, page)
    page_data = pagination_data(paginator, page)
    return render(request, 'blog/index.html', locals())

def tag(request, tag_id):
    # t = models.Tag.objects.get(id=tag_id)
    t = get_object_or_404(models.Tag, id=tag_id)
    if t.name == "全部":
        entries = models.Entry.objects.all()
    else:
        entries = models.Entry.objects.filter(tag=t)

    page = request.GET.get('page', 1)
    entry_list, paginator = make_paginator(entries, page)
    page_data = pagination_data(paginator, page)
    return render(request, 'blog/index.html', locals())

def search(request):
    keyword = request.GET.get('keyword', None)
    if not keyword:
        error_msg = "请输入关键字"
        return render(request, 'blog/index.html', locals())
    entries = models.Entry.objects.filter(Q(title__icontains=keyword)
                                          | Q(body__icontains=keyword)
                                          | Q(abstract__icontains=keyword))
    page = request.GET.get('page', 1)
    entry_list, paginator = make_paginator(entries, page)
    page_data = pagination_data(paginator, page)
    return render(request, 'blog/index.html', locals())

def archives(request, year, month):
    entries = models.Entry.objects.filter(created_time__year=year, created_time__month=month)
    page = request.GET.get('page', 1)
    entry_list, paginator = make_paginator(entries, page)
    page_data = pagination_data(paginator, page)
    return render(request, 'blog/index.html', locals())

def permission_denied(request, exception=None, template_name='403.html'):
    return render(request, template_name, locals())

def page_not_found(request, exception=None, template_name='404.html'):
    return render(request, template_name, locals())

def page_error(request, exception=None, template_name='500.html'):
    return render(request, template_name, locals())

def login(request):
    import requests
    import json
    from django.conf import settings
    code = request.GET.get('code', None)
    if code is None:
        return redirect('/')
    access_token_url = 'https://api.weibo.com/oauth2/access_token?client_id=%s&client_secret=%s&grant_type=authorization_code&redirect_uri=http://www.chunqingawei.com/login/&code=%s'\
                         % (settings.CLIENT_ID, settings.APP_SECRET, code)
    ret = requests.post(access_token_url)
    data = ret.text
    data_dict = json.loads(data)

    token = data_dict['access_token']
    uid = data_dict['uid']

    request.session['token'] = token
    request.session['uid'] = uid
    request.session['login'] = True

    user_info_url = 'https://api.weibo.com/2/users/show.json?access_token=%s&uid=%s' % (token, uid)
    user_info = requests.get(user_info_url)
    user_info_dict = json.loads(user_info.text)

    request.session['screen_name'] = user_info_dict['screen_name']
    request.session['profile_image_url'] = user_info_dict['profile_image_url']

    return redirect(request.GET.get('next', '/'))

def logout(request):
    if request.session['login']:
       del request.session['login']
       del request.session['uid']
       del request.session['token']
       del request.session['screen_name']
       del request.session['profile_image_url']
    # request.session.flush()
       return redirect(request.GET.get('next', '/'))
    else:
        return redirect('/')

def reply(request, comment_id):
    if not request.session.get('login', None) and not request.user.is_authenticated:
        return redirect('/')
    parent_comment = get_object_or_404(comment_models.Comment, id=comment_id)
    return render(request, 'blog/reply.html', locals())









