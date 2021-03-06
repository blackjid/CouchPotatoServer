from couchpotato import index
from couchpotato.api import addApiView
from couchpotato.core.event import fireEvent, addEvent
from couchpotato.core.helpers.request import getParam, jsonified
from couchpotato.core.helpers.variable import isDict
from couchpotato.core.logger import CPLog
from couchpotato.core.plugins.base import Plugin
from couchpotato.environment import Env
from flask.globals import request
from flask.helpers import url_for
import os

log = CPLog(__name__)


class Userscript(Plugin):

    version = 1

    def __init__(self):
        addApiView('userscript.get/<path:filename>', self.getUserScript, static = True)
        addApiView('userscript', self.iFrame)
        addApiView('userscript.add_via_url', self.getViaUrl)

        addEvent('userscript.get_version', self.getVersion)

    def getUserScript(self, filename = ''):

        params = {
            'includes': fireEvent('userscript.get_includes', merge = True),
            'excludes': fireEvent('userscript.get_excludes', merge = True),
            'version': self.getVersion(),
            'api': '%suserscript/' % url_for('api.index').lstrip('/'),
            'host': request.host_url,
        }

        script = self.renderTemplate(__file__, 'template.js', **params)
        self.createFile(os.path.join(Env.get('cache_dir'), 'couchpotato.user.js'), script)

        from flask.helpers import send_from_directory
        return send_from_directory(Env.get('cache_dir'), 'couchpotato.user.js')

    def getVersion(self):

        versions = fireEvent('userscript.get_provider_version')

        version = self.version
        for v in versions:
            version += v

        return version

    def iFrame(self):
        return index()

    def getViaUrl(self):

        url = getParam('url')

        params = {
            'url': url,
            'movie': fireEvent('userscript.get_movie_via_url', url = url, single = True)
        }
        if not isDict(params['movie']):
            log.error('Failed adding movie via url: %s' % url)
            params['error'] = params['movie'] if params['movie'] else 'Failed getting movie info'

        return jsonified(params)
