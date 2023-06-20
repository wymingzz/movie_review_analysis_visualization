import pandas as pd

import getdata


class Movie:

    def __init__(self, name: str = None, Id=None):
        self.name = name
        self.url = 'https://movie.douban.com/subject/{}/'.format(Id)
        self.bar_timeline = getdata.get_bar_timeline(name)
        self.wordcloud_timeline = getdata.get_wordcloud_timeline(name)
        self.star_radar = getdata.get_radar(name)
        self.pie_timeline = getdata.get_pie_timeline(name)
