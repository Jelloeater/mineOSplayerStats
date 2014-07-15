class WithinContext(object):

    # def __init__(self, context):
    #     print 'WithinContext.__init__(%s)' % context

    def do_something(self,text):
        print 'WithinContext.do_something() ' + text

    # def __del__(self):
    #     print 'WithinContext.__del__'


class Context(object):

    # def __init__(self):
    #     print 'Context.__init__()'

    def __enter__(self):
        print 'Context.__enter__()'
        return WithinContext()

    def __exit__(self, exc_type, exc_val, exc_tb):
        print 'Context.__exit__()'

with Context() as c:
    c.do_something('hi')
    c.do_something('hi2')

