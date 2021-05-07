# -*- coding: utf-8 -*-
import scrapy
from soccer_data.items import SoccerDataItem
import json


class ChampdasSpider(scrapy.Spider):
    name = 'aiguo'
    years = [2019]
    max_round = 30
    start_urls = 'http://data.champdas.com/match/scheduleDetail-1-{year}-{round}.html'

    def start_requests(self):
        for year in self.years:
            for match_round in range(1, self.max_round + 1):
                yield scrapy.Request(url=self.start_urls.format(year=year, round=match_round),
                                     meta={'year': year, 'match_round': match_round},
                                     callback=self.parse_url)

    def parse_url(self, response):
        year = response.meta['year']
        match_round = response.meta['match_round']
        match_reports = response.xpath('//span[@class="matchNote"]/a')
        for match_report in match_reports:
            url = match_report.xpath('./@href').extract_first(default='')
            full_url = response.urljoin(url)
            yield scrapy.Request(url=full_url, meta={'year': year, 'match_round': match_round},
                                 callback=self.parse_website)

    def parse_website(self, response):
        item = SoccerDataItem()

        item['home_team'] = response.xpath('//div[@class="l_team"]').xpath('string(.)').extract_first(default='')
        item['away_team'] = response.xpath('//div[@class="r_team"]').xpath('string(.)').extract_first(default='')
        item['home_team_score'] = int(response.xpath('//div[@class="match_score"]/span[1]')
                                      .xpath('string(.)').extract_first(default=-1))
        item['away_team_score'] = int(response.xpath('//div[@class="match_score"]/span[2]')
                                      .xpath('string(.)').extract_first(default=-1))
        item['home_team_id'] = response.xpath("//input[@id='hometeamId']/@value").extract_first('')
        item['away_team_id'] = response.xpath("//input[@id='guestteamId']/@value").extract_first('')
        item['season'] = response.meta['year']
        item['round'] = response.meta['match_round']
        item['url'] = response.url
        item['matchID'] = response.url[response.url.index('-')+1:response.url.index('.html')]


        Cookie = "UM_distinctid=17636463b25338-0d73ed95390153-c791039-100200-17636463b265a4; JSESSIONID=36CF389456A8DC63B02CCB4F836A3B8C; CNZZDATA1259391208=1368675017-1607228340-http%253A%252F%252Fwww.champdas.com%252F%7C1619432402"

        headers = {
            'User-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.85 Safari/537.36",  # 设置get请求的User-Agent，用于伪装浏览器UA
            'Cookie': Cookie,
            'Connection': 'keep-alive',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9',
            'Host': 'data.champdas.com',
            'Referer': response.url
        }
        matchId = item['matchID']


        urls = ["http://data.champdas.com/getMatchStaticListAjax.html",
                "http://data.champdas.com/getMatchAttackAjax.html",
                "http://data.champdas.com/getMatchDefencesRateAjax.html"
                ]
        for url in urls:

            for i in range(1,3):
                data = {
                    'matchId':matchId,
                    'half':'{}'.format(i)
                }

                yield scrapy.FormRequest(url=url, formdata=data, headers=headers, meta={'item': item, 'url':url,'half':i},
                                     callback=self.parseHalfTeamData)

    def parseHalfTeamData(self,response):
        item = response.meta['item']
        url = response.meta['url']
        half = response.meta['half']#1上半场2下半场

        if str(half) == "1":
            if url == "http://data.champdas.com/getMatchStaticListAjax.html":
                item['StaticList_first'] = response.text
            elif url == "http://data.champdas.com/getMatchAttackAjax.html":
                item['Attack_first'] = response.text
            else:
                item['DefencesRate_first'] = response.text
        else:
            if url == "http://data.champdas.com/getMatchStaticListAjax.html":
                item['StaticList_second'] = response.text
            elif url == "http://data.champdas.com/getMatchAttackAjax.html":
                item['Attack_second'] = response.text
            else:
                item['DefencesRate_second'] = response.text


        return item

