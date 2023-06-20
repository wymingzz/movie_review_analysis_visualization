from django.shortcuts import render
from pathlib import Path
import data

from getdata import get_id, get_data


def index(request):
    if request.method == 'POST':
        # 处理POST请求的逻辑
        Name = request.POST.get('name')
        # 进一步的处理和验证...
        name, Id = get_id(Name)
        folder_path = Path('data/{}'.format(name))
        if not folder_path.is_dir():
            if name is None and Id is None:
                return render(request, 'index.html', {'msg': '没有该电影《{}》'.format(Name)})
            if not get_data(Id, name):
                return render(request, 'index.html', {'msg': '数据获取错误'})
        movie = data.Movie(name, Id)
        context = {
            'new_button': '<button onclick="openNewPage()" style="margin: 0 auto;text-align: center;">点击前往豆瓣主页</button>',
            'movie_url': movie.url,
            'title': movie.name + '电影评论数据可视化',
            'pie_title': '情感分布图',
            'pie_timeline': movie.pie_timeline.render_embed(),
            'bar_title': '使用频率前10的单词',
            'bar_timeline': movie.bar_timeline.render_embed(),
            'star_title': '评分分布',
            'star_radar': movie.star_radar.render_embed(),
            'wordcloud_title': '各评分词云',
            'wordcloud_timeline': movie.wordcloud_timeline.render_embed(),
        }
        # 返回响应
        return render(request, 'index.html', context)
    else:
        # 处理GET请求的逻辑
        return render(request, 'index.html')
