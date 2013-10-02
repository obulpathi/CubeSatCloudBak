from twisted.spread import pb
from twisted.cred import checkers, portal
from zope.interface import implements

class TodoList:
    def __init__(self):
        self.items = []

    def listItems(self):
        return self.items[:] # return copy of list

    def addItem(self, item):
        self.items.append(item)
        return len(self.items) - 1

    def deleteItem(self, index):
        del(self.items[index])

class UserPerspective(pb.Avatar):
    def __init__(self, todoList):
        self.todoList = todoList

    def perspective_listItems(self):
        return self.todoList.listItems()

class AdminPerspective(UserPerspective):
    def __init__(self, todoList):
        self.todoList = todoList

    def perspective_addItem(self, item):
        return self.todoList.addItem(item)

    def perspective_deleteItem(self, index):
        return self.todoList.deleteItem(index)

class TestRealm(object):
    implements(portal.IRealm)

    def __init__(self, todoList):
        self.todoList = todoList

    def requestAvatar(self, avatarId, mind, *interfaces):
        if not pb.IPerspective in interfaces:
            raise NotImplementedError, "No supported avatar interface."
        else:
            if avatarId == 'admin':
                avatar = AdminPerspective(self.todoList)
            else:
                avatar = UserPerspective(self.todoList)
            return pb.IPerspective, avatar, lambda: None

if __name__ == "__main__":
    import sys
    from twisted.internet import reactor
    p = portal.Portal(TestRealm(TodoList()))
    p.registerChecker(
        checkers.InMemoryUsernamePasswordDatabaseDontUse(
        admin='aaa',
        guest='bbb'))
    reactor.listenTCP(8789, pb.PBServerFactory(p))
    reactor.run()
