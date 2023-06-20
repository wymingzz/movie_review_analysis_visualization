import re
from collections import Counter
from pathlib import Path
from urllib.parse import quote

import jieba
import pandas as pd
import requests
from lxml import etree
from snownlp import SnowNLP
from textblob import TextBlob
from pyecharts.charts import Pie, Bar, Radar, WordCloud, Timeline
from pyecharts import options as opts

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,'
              'application/signed-exchange;v=b3;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Cookie': 'bid=9Bz5zHy15xM; ll="118249"; _ga=GA1.2.345052572.1684829755; __yadk_uid=48MjgDSYd52OLp7c4TMitF5JMt3O2OHc; _vwo_uuid_v2=DDC2EC19CFEA1995038CA625A2A82A110|80ed821bfe2b96b6a6c1257f839727d5; push_noty_num=0; push_doumail_num=0; __utmv=30149280.27088; Hm_lvt_16a14f3002af32bf3a75dfe352478639=1684848082; _pk_id.100001.4cf6=53105001a7ca5fcd.1684829758.; __utma=30149280.345052572.1684829755.1686038356.1686066090.5; __utmc=30149280; __utmz=30149280.1686066090.5.4.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utmb=30149280.1.10.1686066090; _pk_ref.100001.4cf6=%5B%22%22%2C%22%22%2C1686066092%2C%22https%3A%2F%2Fwww.google.com%2F%22%5D; _pk_ses.100001.4cf6=1; __utma=223695111.345052572.1684829755.1686038356.1686066092.5; __utmb=223695111.0.10.1686066092; __utmc=223695111; __utmz=223695111.1686066092.5.4.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); ap_v=0,6.0; __gads=ID=435217f12192f2a0-22b8eff13be10068:T=1684829760:RT=1686066098:S=ALNI_MZmsk5TkLnTic5hcmtLBUSoWKzRcw; __gpi=UID=00000c09cefa6db6:T=1684829760:RT=1686066098:S=ALNI_MYdzT6cNd5u4F3COspntXx1HK2S6g; dbcl2="270883185:snjom+zmU84"; ck=c0ne; frodotk_db="5cb14227976aa1721613c676c63fe456"',
    'Host': 'movie.douban.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 '
                  'Safari/537.36',
}

stopwords = [line.strip() for line in open('data/stopwords.txt', 'r', encoding='utf-8').readlines()]


def tokenize(comment):
    words = jieba.lcut(comment)
    filtered_words = [word for word in words if
                      len(word) > 1 and word != '\r\n' and word not in stopwords and not word.isdigit()]
    return filtered_words


def analyze_sentiment(comment):
    if re.search('[a-zA-Z]', comment):  # 如果评论中包含英文字符
        blob = TextBlob(comment)
        sentiment = blob.sentiment.polarity
    else:
        s = SnowNLP(comment)
        sentiment = s.sentiments

    if sentiment < 0:
        return "负面情感"  # Negative sentiment
    elif sentiment > 0:
        return "正面情感"  # Positive sentiment
    else:
        return "中性情感"  # Neutral sentiment


def get_top10(data):
    most_common = data.most_common()

    # 判断列表长度是否小于等于10
    if len(most_common) <= 10:
        result = most_common
    else:
        result = most_common[:10]

    return result


def to_excel(data, columns, name: str):
    df = pd.DataFrame(data, columns=columns)
    df.to_excel(name, index=False)


def get_data(ID, Name: str):
    if ID is None:
        return False
    try:
        if Name is None:
            url = 'https://movie.douban.com/subject/{}/'.format(str(ID))
            res = requests.get(url, headers=headers)
            html = res.text
            xp = etree.HTML(html)
            Name = xp.xpath('//*[@id="content"]/h1/span[1]/text()')
        folder_path = Path('data/{}'.format(Name))
        if not folder_path.is_dir():
            folder_path.mkdir()
        file_path = Path('data/{}/{}.xlsx'.format(Name, Name))
        if not file_path.exists():
            index = 1
            df = []
            columns = ['index', 'commenter', 'star', 'comment']
            for i in range(0, 201, 100):
                url = "https://movie.douban.com/subject/{}/comments?start={}&limit=100&status=P&sort=new_score".format(
                    str(ID), str(i))
                res = requests.get(url, headers=headers)
                html = res.text
                xp = etree.HTML(html)
                lis = xp.xpath('//*[@id="comments"]/div')
                for li in lis:
                    name = li.xpath('div[2]/h3/span[2]/a/text()')
                    star = li.xpath('div[2]/h3/span[2]/span[2]/@class')
                    comment = li.xpath('div[2]/p/span/text()')
                    if len(star) == 0:
                        continue
                    else:
                        name = name[0]
                        star = star[0][7]
                        comment = comment[0]
                    df.append([index, name, star, comment])
                    index += 1
            res = pd.DataFrame(df, columns=columns)
            res['star'] = res['star'].astype(str)
            res.to_excel('data/{}/{}.xlsx'.format(Name, Name), index=False)
            comments1 = res.loc[res['star'] == '1', 'comment'].values
            comments2 = res.loc[res['star'] == '2', 'comment'].values
            comments3 = res.loc[res['star'] == '3', 'comment'].values
            comments4 = res.loc[res['star'] == '4', 'comment'].values
            comments5 = res.loc[res['star'] == '5', 'comment'].values
            stars = res['star'].value_counts()
            star_index = ['1分', '2分', '3分', '4分', '5分']
            star_columns = ['评分', '次数']
            counter_words_index = ['单词', '次数']
            comment_sentiment_index = ['情感趋向', '次数']
            star_list = [stars.get('1', 0), stars.get('2', 0), stars.get('3', 0), stars.get('4', 0), stars.get('5', 0)]
            star = pd.DataFrame(list(zip(star_index, star_list)), columns=star_columns)
            star.to_excel('data/{}/star.xlsx'.format(Name), index=False)
            comment_words_1 = []
            comment_words_2 = []
            comment_words_3 = []
            comment_words_4 = []
            comment_words_5 = []
            comment_words = []
            comment_sentiment_1 = []
            comment_sentiment_2 = []
            comment_sentiment_3 = []
            comment_sentiment_4 = []
            comment_sentiment_5 = []
            comment_sentiment = []
            for comment in comments1:
                comment_words_1.extend(tokenize(comment))
                comment_sentiment_1.append(analyze_sentiment(comment))
            for comment in comments2:
                comment_words_2.extend(tokenize(comment))
                comment_sentiment_2.append(analyze_sentiment(comment))
            for comment in comments3:
                comment_words_3.extend(tokenize(comment))
                comment_sentiment_3.append(analyze_sentiment(comment))
            for comment in comments4:
                comment_words_4.extend(tokenize(comment))
                comment_sentiment_4.append(analyze_sentiment(comment))
            for comment in comments5:
                comment_words_5.extend(tokenize(comment))
                comment_sentiment_5.append(analyze_sentiment(comment))
            comment_words.extend(comment_words_1)
            comment_words.extend(comment_words_2)
            comment_words.extend(comment_words_3)
            comment_words.extend(comment_words_4)
            comment_words.extend(comment_words_5)
            comment_sentiment.extend(comment_sentiment_1)
            comment_sentiment.extend(comment_sentiment_2)
            comment_sentiment.extend(comment_sentiment_3)
            comment_sentiment.extend(comment_sentiment_4)
            comment_sentiment.extend(comment_sentiment_5)
            comment_words_1 = Counter(comment_words_1)
            comment_words_2 = Counter(comment_words_2)
            comment_words_3 = Counter(comment_words_3)
            comment_words_4 = Counter(comment_words_4)
            comment_words_5 = Counter(comment_words_5)
            comment_words = Counter(comment_words)
            to_excel(comment_words_1.items(), counter_words_index, 'data/{}/comment_words_1.xlsx'.format(Name))
            to_excel(comment_words_2.items(), counter_words_index, 'data/{}/comment_words_2.xlsx'.format(Name))
            to_excel(comment_words_3.items(), counter_words_index, 'data/{}/comment_words_3.xlsx'.format(Name))
            to_excel(comment_words_4.items(), counter_words_index, 'data/{}/comment_words_4.xlsx'.format(Name))
            to_excel(comment_words_5.items(), counter_words_index, 'data/{}/comment_words_5.xlsx'.format(Name))
            to_excel(comment_words.items(), counter_words_index, 'data/{}/comment_words.xlsx'.format(Name))
            comment_words_top10_1 = get_top10(comment_words_1)
            comment_words_top10_2 = get_top10(comment_words_2)
            comment_words_top10_3 = get_top10(comment_words_3)
            comment_words_top10_4 = get_top10(comment_words_4)
            comment_words_top10_5 = get_top10(comment_words_5)
            comment_words_top10 = get_top10(comment_words)
            to_excel(comment_words_top10_1, counter_words_index,
                     'data/{}/comment_words_top10_1.xlsx'.format(Name))
            to_excel(comment_words_top10_2, counter_words_index,
                     'data/{}/comment_words_top10_2.xlsx'.format(Name))
            to_excel(comment_words_top10_3, counter_words_index,
                     'data/{}/comment_words_top10_3.xlsx'.format(Name))
            to_excel(comment_words_top10_4, counter_words_index,
                     'data/{}/comment_words_top10_4.xlsx'.format(Name))
            to_excel(comment_words_top10_5, counter_words_index,
                     'data/{}/comment_words_top10_5.xlsx'.format(Name))
            to_excel(comment_words_top10, counter_words_index, 'data/{}/comment_words_top10.xlsx'.format(Name))
            comment_sentiment_1 = Counter(comment_sentiment_1)
            comment_sentiment_2 = Counter(comment_sentiment_2)
            comment_sentiment_3 = Counter(comment_sentiment_3)
            comment_sentiment_4 = Counter(comment_sentiment_4)
            comment_sentiment_5 = Counter(comment_sentiment_5)
            comment_sentiment = Counter(comment_sentiment)
            to_excel(comment_sentiment_1.items(), comment_sentiment_index,
                     'data/{}/comment_sentiment_1.xlsx'.format(Name))
            to_excel(comment_sentiment_2.items(), comment_sentiment_index,
                     'data/{}/comment_sentiment_2.xlsx'.format(Name))
            to_excel(comment_sentiment_3.items(), comment_sentiment_index,
                     'data/{}/comment_sentiment_3.xlsx'.format(Name))
            to_excel(comment_sentiment_4.items(), comment_sentiment_index,
                     'data/{}/comment_sentiment_4.xlsx'.format(Name))
            to_excel(comment_sentiment_5.items(), comment_sentiment_index,
                     'data/{}/comment_sentiment_5.xlsx'.format(Name))
            to_excel(comment_sentiment.items(), comment_sentiment_index,
                     'data/{}/comment_sentiment.xlsx'.format(Name))

    except Exception as e:
        print("get_data is ERROR: ", e)
        return False
    return True


def get_id(name: str):
    try:
        url1 = 'https://movie.douban.com/j/subject_suggest?q='
        url2 = quote(name)  # URL只允许一部分ASCII字符，其他字符（如汉字）是不符合标准的，此时就要进行编码。
        url = url1 + url2  # 生成针对该剧的链接，上面链接红字部分即为编码的name
        html = requests.get(url, headers=headers)  # 访问链接，获取html页面的内容
        html = html.content.decode()  # 对html的内容解码为utf-8格式
        html_list = html.replace('\/', '/')  # 将html中的\/全部转换成/，只是为了看着方便（不换也行）
        html_list = html_list.split('},{')  # 将html页面中的每一个条目提取为列表的一个元素。
        # 定义正则，目的是从html中提取想要的信息（根据title提取id）
        # 匹配剧名name
        str_title = '"title":"' + name + '"'
        pattern_title = re.compile(str_title)
        # 匹配该剧的id值
        str_id = '"id":"' + '[0-9]*'
        pattern_id = re.compile(str_id)

        # 从html_list中的每个item中提取对应的ID值
        id_list = []  # ID存放列表
        for l in html_list:  # 遍历html_list
            find_results_title = re.findall(pattern_title, l, flags=0)  # 找到匹配该剧name的条目item
            if find_results_title != []:  # 如果有title=name的条目，即如果有匹配的结果
                find_results_id = re.findall(pattern_id, l, flags=0)  # 从该匹配的item中的寻找对应的id之
                id_list.append(find_results_id)  # 将寻找到的id值储存在id_list中

        # 可能匹配到了多个ID（可能是同名不同剧），根据产生的id的数量，使剧名name匹配产生的id，使两个list相匹配
        name_list = [name] * len(id_list)

        # 对id_list的格式进行修整，使之成为标准列表格式
        id_list = str(id_list).replace('[', '').replace(']', '').replace("'", '').replace('"id":"', '').replace(' ', '')
        id_list = id_list.split(',')

    except Exception as e:  # 如果不能正常运行上述代码（不能访问网页等），输出未成功的剧名name。
        print(e)
        print('ERROR:', name)
        return None, None
    if len(name_list) == 0 or len(id_list) == 0:
        return None, None
    return name_list[0], id_list[0]


def get_pie(data):
    if len(data) == 0:
        return Pie(init_opts=opts.InitOpts(width="600px", height="500px"))
    index = data.index.tolist()
    values = data['次数'].tolist()
    pie_chart = (
        Pie(init_opts=opts.InitOpts(width="600px", height="500px"))
        .add(
            "",
            [list(z) for z in zip(index, values)],
            radius=["40%", "75%"],
            center=["50%", "50%"],
            rosetype="area",
            label_opts=opts.LabelOpts(is_show=False),
        )
        .set_global_opts(
            legend_opts=opts.LegendOpts(orient="vertical", pos_top="15%", pos_left="2%"),
        )
    )
    return pie_chart


def get_bar(data):
    if len(data) == 0:
        # 数据为空时返回一个空的饼图
        return Bar(init_opts=opts.InitOpts(width="600px", height="500px"))
    # 提取单词和次数列数据
    word_list = data.index.tolist()
    count_list = data['次数'].tolist()

    # 创建 Bar 实例
    bar_chart = (
        Bar(init_opts=opts.InitOpts(width="600px", height="500px"))
        .add_xaxis(word_list)
        .add_yaxis("次数", count_list)
        .set_global_opts(
            xaxis_opts=opts.AxisOpts(axislabel_opts=opts.LabelOpts(rotate=45)),
        )
    )
    return bar_chart


def get_radar(name: str):
    data = pd.read_excel('data/{}/star.xlsx'.format(name), sheet_name='Sheet1', index_col=0)
    # 提取评分和次数列数据
    if len(data) == 0:
        return Radar(init_opts=opts.InitOpts(width="600px", height="500px"))
    count_list = data['次数'].tolist()

    # 创建 Radar 实例
    radar_chart = (
        Radar(init_opts=opts.InitOpts(width="600px", height="500px"))
        .add_schema(
            schema=[
                opts.RadarIndicatorItem(name="1分", max_=max(count_list)),
                opts.RadarIndicatorItem(name="2分", max_=max(count_list)),
                opts.RadarIndicatorItem(name="3分", max_=max(count_list)),
                opts.RadarIndicatorItem(name="4分", max_=max(count_list)),
                opts.RadarIndicatorItem(name="5分", max_=max(count_list)),
            ]
        )
        .add("次数", [count_list], color="#0066CC")
        .set_series_opts(label_opts=opts.LabelOpts(is_show=False))
    )

    return radar_chart


def get_wordcloud(data):
    if len(data) == 0:
        return WordCloud(init_opts=opts.InitOpts(width="600px", height="500px"))
    # 提取单词和次数列数据
    word_list = data.index.tolist()
    count_list = data['次数'].tolist()

    # 创建 WordCloud 实例
    wordcloud = (
        WordCloud(init_opts=opts.InitOpts(width="600px", height="500px"))
        .add("", zip(word_list, count_list), word_size_range=[20, 100])
    )

    return wordcloud


def get_pie_timeline(name: str):
    comment_sentiment_1 = pd.read_excel('data/{}/comment_sentiment_1.xlsx'.format(name), sheet_name='Sheet1',
                                        index_col=0)
    comment_sentiment_2 = pd.read_excel('data/{}/comment_sentiment_2.xlsx'.format(name), sheet_name='Sheet1',
                                        index_col=0)
    comment_sentiment_3 = pd.read_excel('data/{}/comment_sentiment_3.xlsx'.format(name), sheet_name='Sheet1',
                                        index_col=0)
    comment_sentiment_4 = pd.read_excel('data/{}/comment_sentiment_4.xlsx'.format(name), sheet_name='Sheet1',
                                        index_col=0)
    comment_sentiment_5 = pd.read_excel('data/{}/comment_sentiment_5.xlsx'.format(name), sheet_name='Sheet1',
                                        index_col=0)
    comment_sentiment = pd.read_excel('data/{}/comment_sentiment.xlsx'.format(name), sheet_name='Sheet1',
                                      index_col=0)
    sentiment_1_pie = get_pie(comment_sentiment_1)
    sentiment_2_pie = get_pie(comment_sentiment_2)
    sentiment_3_pie = get_pie(comment_sentiment_3)
    sentiment_4_pie = get_pie(comment_sentiment_4)
    sentiment_5_pie = get_pie(comment_sentiment_5)
    sentiment_pie = get_pie(comment_sentiment)
    return get_timeline(
        [sentiment_1_pie, sentiment_2_pie, sentiment_3_pie, sentiment_4_pie, sentiment_5_pie, sentiment_pie])


def get_wordcloud_timeline(name: str):
    comment_words_1 = pd.read_excel('data/{}/comment_words_1.xlsx'.format(name), sheet_name='Sheet1', index_col=0)
    comment_words_2 = pd.read_excel('data/{}/comment_words_2.xlsx'.format(name), sheet_name='Sheet1', index_col=0)
    comment_words_3 = pd.read_excel('data/{}/comment_words_3.xlsx'.format(name), sheet_name='Sheet1', index_col=0)
    comment_words_4 = pd.read_excel('data/{}/comment_words_4.xlsx'.format(name), sheet_name='Sheet1', index_col=0)
    comment_words_5 = pd.read_excel('data/{}/comment_words_5.xlsx'.format(name), sheet_name='Sheet1', index_col=0)
    comment_words = pd.read_excel('data/{}/comment_words.xlsx'.format(name), sheet_name='Sheet1', index_col=0)
    words_1_wordcloud = get_wordcloud(comment_words_1)
    words_2_wordcloud = get_wordcloud(comment_words_2)
    words_3_wordcloud = get_wordcloud(comment_words_3)
    words_4_wordcloud = get_wordcloud(comment_words_4)
    words_5_wordcloud = get_wordcloud(comment_words_5)
    words_wordcloud = get_wordcloud(comment_words)
    return get_timeline(
        [words_1_wordcloud, words_2_wordcloud, words_3_wordcloud, words_4_wordcloud, words_5_wordcloud,
         words_wordcloud])


def get_bar_timeline(name: str):
    comment_words_top10_1 = pd.read_excel('data/{}/comment_words_top10_1.xlsx'.format(name), sheet_name='Sheet1',
                                          index_col=0)
    comment_words_top10_2 = pd.read_excel('data/{}/comment_words_top10_2.xlsx'.format(name), sheet_name='Sheet1',
                                          index_col=0)
    comment_words_top10_3 = pd.read_excel('data/{}/comment_words_top10_3.xlsx'.format(name), sheet_name='Sheet1',
                                          index_col=0)
    comment_words_top10_4 = pd.read_excel('data/{}/comment_words_top10_4.xlsx'.format(name), sheet_name='Sheet1',
                                          index_col=0)
    comment_words_top10_5 = pd.read_excel('data/{}/comment_words_top10_5.xlsx'.format(name), sheet_name='Sheet1',
                                          index_col=0)
    comment_words_top10 = pd.read_excel('data/{}/comment_words_top10.xlsx'.format(name), sheet_name='Sheet1',
                                        index_col=0)
    words_top10_1_bar = get_bar(comment_words_top10_1)
    words_top10_2_bar = get_bar(comment_words_top10_2)
    words_top10_3_bar = get_bar(comment_words_top10_3)
    words_top10_4_bar = get_bar(comment_words_top10_4)
    words_top10_5_bar = get_bar(comment_words_top10_5)
    words_top10_bar = get_bar(comment_words_top10)
    return get_timeline(
        [words_top10_1_bar, words_top10_2_bar, words_top10_3_bar, words_top10_4_bar, words_top10_5_bar,
         words_top10_bar])


def get_timeline(datas):
    titles = ['1星评论', '2星评论', '3星评论', '4星评论', '5星评论', '汇总']
    timeline = Timeline(init_opts=opts.InitOpts(width="600px", height="500px"))
    for i in range(len(datas)):
        timeline.add(datas[i], titles[i])
    return timeline
