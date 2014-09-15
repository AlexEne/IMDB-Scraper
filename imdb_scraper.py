import requests
import matplotlib.pyplot as plt
import bs4
import codecs
import time
import pandas as pd
import os.path


def scrap_page(start):
    payload = {'sort': 'num_votes,desc', 'start': start, 'title_type': 'feature'}
    req = requests.get('http://www.imdb.com/search/title', params=payload)
    bs = bs4.BeautifulSoup(req.content)
    results = bs.findChild('table', {'class': 'results'})
    while req.status_code != 200 or not results:
        time.sleep(1)  # try again
        req = requests.get('http://www.imdb.com/search/title', params=payload)
        bs = bs4.BeautifulSoup(req.text)
        results = bs.findChild('table', {'class': 'results'})

    titles = results.findChildren('td', 'title')

    for i, title in enumerate(titles[:-1]):
        name = title.findAll('a', href=True)[0].text
        year = title.find('span', 'year_type').text
        rating = title.select('.value')[0].text
        d = title.findChild('span', {'class': 'runtime'})
        duration = '0'
        if d:
            duration = d.text
        g = title.findChild('span', {'class': 'genre'})
        if not g:
            continue  # no gender for this movie, just skip it.
        genres = g.findChildren('a')
        genre = '|'.join(gen.text for gen in genres)
        p = title.parent
        num_votes = p.findChild('td', {'class': 'sort_col'}).text
        num_votes = num_votes.replace(',', '')
        # print ','.join([name, year, rating, duration, num_votes, genre])
        with codecs.open('movies.csv', 'a', 'utf-8') as f:
            line = '\t'.join([name, year, rating, duration, num_votes, genre])
            f.write(line + '\n')
    return i + 1


def process_data(csv_file):
    n = ['name', 'year', 'score', 'duration', 'votes', 'genre']
    data = pd.read_csv(csv_file, names=n, delimiter='\t', encoding='utf-8').dropna()#, engine='python'
    data['duration'] = [float(r.split(' ')[0]) for r in data.duration]
    data['year'] = [float(y[1:-1]) for y in data.year]

    genres = set()
    for movie in data.genre:
        genres.update(movie.split('|'))
    genres = sorted(genres)
    for genre in genres:
        data[genre] = [genre in movie.split('|') for movie in data.genre]
    return data


def plot_axis(ax, data_x, data_y, title='', show_x=False, show_y=False):
    ax.scatter(data_x, data_y, alpha=0.3, color="#02779E", edgecolor="#02779E")
    ax.axes.get_xaxis().set_visible(show_x)
    ax.axes.get_yaxis().set_visible(show_y)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    ax.spines['left'].set_visible(False)
    if title:
        ax.set_title(title)
    # ax.spines['bottom'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    for y in range(1, 11):
        ax.plot(range(1908, 2015), [y] * len(range(1908, 2015)), "-", lw=0.5, color="black", alpha=0.3)


def main():
    if not os.path.isfile('movies.csv'):
        total_scraped = 0
        while total_scraped < 10000:
            total_scraped += scrap_page(total_scraped + 1)
            print 'Scraped {0}'.format(total_scraped)
            time.sleep(1)  # be nice

    data = process_data('movies.csv')

    #Some interesting old movies because they have an unusual high number of votes compared to that period
    #print data[(data.year < 1950) & (data.votes > 100000)]

    #fig = plt.figure(facecolor='white', figsize=(9, 9))

    genres = ['Action', 'Adult', 'Adventure', 'Animation', 'Biography', 'Comedy', 'Crime', 'Drama',
              'Family', 'Fantasy', 'Film-Noir', 'History', 'Horror', 'Music', 'Musical', 'Mystery', 'Romance',
              'Sci-Fi', 'Sport', 'Thriller', 'War', 'Western']

    fig = plt.figure(facecolor='white', figsize=(9, 9))
    ax1 = fig.add_subplot(5, 5, 1)
    plot_axis(ax1, data.year, data.score, title='Overall score/year distribution', show_y=True)

    for i, genre in enumerate(genres):
        d = data[(data[genre] == True)]
        pos = i+2
        if pos >= 4:
            pos += 2
        ax = fig.add_subplot(5, 5, pos, sharex=ax1, sharey=ax1, title=genre)
        plot_axis(ax, d.year, d.score)
        if pos > 20:
            ax.axes.get_xaxis().set_visible(True)
            for label in ax.xaxis.get_ticklabels():
                label.set_rotation(45)
        if (pos-1) % 5 == 0:
            ax.axes.get_yaxis().set_visible(True)

    #Plot the number of votes for each year. This plot is bad as a line plot it should be a bar plot.
    #year_data = data.groupby('year').votes.sum()
    #ax = fig.add_subplot(1, 1, 1)
    #ax.plot(year_data.index, year_data.values, '-')

    fig.subplots_adjust(wspace=0.4, hspace=0.3)
    plt.xlim(1908, 2016)
    plt.ylim(0, 10)
    plt.show()


if __name__ == '__main__':
    main()