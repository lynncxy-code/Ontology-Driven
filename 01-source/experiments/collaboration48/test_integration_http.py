"""Read-only HTTP checks against the initialized isolated 5148 environment."""
import http.client
import json
import unittest


class IntegrationHTTPTests(unittest.TestCase):
    def call(self, method, path, data=None, cookie=None, origin='http://127.0.0.1:5148'):
        c = http.client.HTTPConnection('127.0.0.1',5148,timeout=10)
        headers = {'Content-Type':'application/json'}
        if origin:
            headers['Origin']=origin
        if cookie:
            headers['Cookie']=cookie
        c.request(method,path,json.dumps(data) if data is not None else None,headers)
        r=c.getresponse()
        result=(r.status,dict(r.getheaders()),r.read().decode())
        c.close()
        return result

    def test_anonymous_existing_api_blocked(self):
        self.assertEqual(self.call('GET','/api/v2/ontology/datasets')[0],401)

    def test_deep_link_keeps_return(self):
        status, headers, _=self.call('GET','/interaction?feature=routes&nexus=true')
        self.assertEqual(status,302)
        self.assertIn('%26nexus%3Dtrue',headers['Location'])

    def test_cross_origin_write_rejected(self):
        self.assertEqual(self.call('POST','/_collab48/api/login',{},origin='http://example.invalid')[0],403)

    def test_login_legacy_page_and_member_list(self):
        status, headers, _=self.call('POST','/_collab48/api/login',dict(account='admin',password='DemoAdmin2026!'))
        self.assertEqual(status,200)
        cookie=headers['Set-Cookie'].split(';')[0]
        self.assertIn('navigation.js',self.call('GET','/nexus',cookie=cookie)[2])
        self.assertIn('ontology_graph',self.call('GET','/nexus',cookie=cookie)[2])
        state=json.loads(self.call('GET','/_collab48/api/state',cookie=cookie)[2])
        self.assertTrue(state['initialized'])
        self.assertIn('editor',[u['account'] for u in state['users']])
        self.assertIn('4.8 联通测试工厂',[p['name'] for p in state['projects']])
        self.call('POST','/_collab48/api/logout',{},cookie=cookie)
        self.assertEqual(self.call('GET','/api/v2/ontology/datasets',cookie=cookie)[0],401)


if __name__=='__main__':
    unittest.main()
