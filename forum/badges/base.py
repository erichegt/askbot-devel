

class BadgeImplementation(object):
    name = ""
    description = ""

    def install(self):
        pass

    def process_job(self):
        raise NotImplementedError