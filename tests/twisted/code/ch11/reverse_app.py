from twisted.application import service
import reverse

application = service.Application("Reverser")
reverserService = reverse.ReverserService()
reverserService.setServiceParent(application)
