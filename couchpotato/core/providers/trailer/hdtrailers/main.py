from BeautifulSoup import SoupStrainer, BeautifulSoup
from couchpotato.core.helpers.variable import mergeDicts
from couchpotato.core.logger import CPLog
from couchpotato.core.providers.trailer.base import TrailerProvider
from string import letters, digits
from urllib import urlencode
import re

log = CPLog(__name__)


class HDTrailers(TrailerProvider):

    urls = {
        'api': 'http://www.hd-trailers.net/movie/%s/',
        'backup': 'http://www.hd-trailers.net/blog/',
    }
    providers = ['apple.ico', 'yahoo.ico', 'moviefone.ico', 'myspace.ico', 'favicon.ico']

    def search(self, group):

        movie_name = group['library']['titles'][0]['title']

        url = self.urls['api'] % self.movieUrlName(movie_name)
        data = self.getCache('hdtrailers.%s' % group['library']['identifier'], url)

        result_data = {}

        did_alternative = False
        for provider in self.providers:
            results = self.findByProvider(data, provider)

            # Find alternative
            if results.get('404') and not did_alternative:
                results = self.findViaAlternative(group)
                did_alternative = True

            result_data = mergeDicts(result_data, results)

        return result_data

    def findViaAlternative(self, group):
        results = {'480p':[], '720p':[], '1080p':[]}

        movie_name = group['library']['titles'][0]['title']

        url = "%s?%s" % (self.url['backup'], urlencode({'s':movie_name}))
        data = self.getCache('hdtrailers.alt.%s' % group['library']['identifier'], url)

        try:
            tables = SoupStrainer('div')
            html = BeautifulSoup(data, parseOnlyThese = tables)
            result_table = html.findAll('h2', text = re.compile(movie_name))

            for h2 in result_table:
                if 'trailer' in h2.lower():
                    parent = h2.parent.parent.parent
                    trailerLinks = parent.findAll('a', text = re.compile('480p|720p|1080p'))
                    try:
                        for trailer in trailerLinks:
                            results[trailer].insert(0, trailer.parent['href'])
                    except:
                        pass

        except AttributeError:
            log.debug('No trailers found in via alternative.')

        return results

    def findByProvider(self, data, provider):

        results = {'480p':[], '720p':[], '1080p':[]}
        try:
            tables = SoupStrainer('table')
            html = BeautifulSoup(data, parseOnlyThese = tables)
            result_table = html.find('table', attrs = {'class':'bottomTable'})


            for tr in result_table.findAll('tr'):
                trtext = str(tr).lower()
                if 'clips' in trtext:
                    break
                if 'trailer' in trtext and not 'clip' in trtext and provider in trtext:
                    nr = 0
                    if 'trailer' not in tr.find('span', 'standardTrailerName').text.lower():
                        continue
                    resolutions = tr.findAll('td', attrs = {'class':'bottomTableResolution'})
                    for res in resolutions:
                        results[str(res.a.contents[0])].insert(0, res.a['href'])
                        nr += 1

            return results

        except AttributeError:
            log.debug('No trailers found in provider %s.' % provider)
            results['404'] = True

        return results

    def movieUrlName(self, string):
        safe_chars = letters + digits + ' '
        r = ''.join([char if char in safe_chars else ' ' for char in string])
        name = re.sub('\s+' , '-', r).lower()

        try:
            int(name)
            return '-' + name
        except:
            return name
