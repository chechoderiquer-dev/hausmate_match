ConnectError: [Errno -2] Name or service not known
Traceback:
File "/mount/src/hausmate_match/app.py", line 647, in <module>
    supa.table(table).insert(payload).execute()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
File "/home/adminuser/venv/lib/python3.13/site-packages/postgrest/_sync/request_builder.py", line 47, in execute
    r = self.request.send()
File "/home/adminuser/venv/lib/python3.13/site-packages/postgrest/base_request_builder.py", line 82, in send
    return self.session.request(
           ~~~~~~~~~~~~~~~~~~~~^
        self.http_method,
        ^^^^^^^^^^^^^^^^^
    ...<4 lines>...
        auth=self.auth,
        ^^^^^^^^^^^^^^^
    )
    ^
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_client.py", line 825, in request
    return self.send(request, auth=auth, follow_redirects=follow_redirects)
           ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_client.py", line 914, in send
    response = self._send_handling_auth(
        request,
    ...<2 lines>...
        history=[],
    )
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_client.py", line 942, in _send_handling_auth
    response = self._send_handling_redirects(
        request,
        follow_redirects=follow_redirects,
        history=history,
    )
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_client.py", line 979, in _send_handling_redirects
    response = self._send_single_request(request)
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_client.py", line 1014, in _send_single_request
    response = transport.handle_request(request)
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_transports/default.py", line 249, in handle_request
    with map_httpcore_exceptions():
         ~~~~~~~~~~~~~~~~~~~~~~~^^
File "/usr/local/lib/python3.13/contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    ~~~~~~~~~~~~~~^^^^^^^
File "/home/adminuser/venv/lib/python3.13/site-packages/httpx/_transports/default.py", line 118, in map_httpcore_exceptions
    raise mapped_exc(message) from exc
