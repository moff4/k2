#!/usr/bin/env python3

from k2.aeon.responses.base_response import Response

class ClientResponse(Response):

	@property
	def ok(self):
		return 200 <= self.code < 300

	@property
	def text(self):
		if isinstance(self._data, str):
			return self._data
		try:
			return self._data.decode()
		except Exception:
			return self._data

    def json(self):
        if self._data:
            return loads(self._data)
        else:
            return {}
