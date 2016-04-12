def get_karma(db, target):
    """ Get Karma
        Return the current amount of karma for a given target, return the
        current value in the database. If the target is not in the database,
        return 0.
    """
    karma = db.execute("SELECT target, karma FROM karma")
    for pair in karma.fetchall():
        if pair[0].lower() == target.lower():
            return int(pair[1])
    return 0


def resolve_alias(db, alias):
    """ Resolve Alias
        Given the name of a potentially aliased target, see if a mapping
        for it exists in the database. If so, return the aliased value,
        otherwise, just return the value given.
    """
    aliases = db.execute("SELECT old, new FROM aliases")
    for pair in aliases.fetchall():
        if pair[0].lower() == alias.lower():
            return pair[1]
    return alias


def resolve_full(db, nick):
    """ Resolve Full
        If the given nickname maps to a full name in the users database,
        return the full name. If not, return the nickname.
    """
    links = db.execute("SELECT full_name, nickname FROM users")
    for pair in links.fetchall():
        if pair[1] is None: continue
        if pair[1].lower() == nick.lower():
            return pair[0]
    return nick


def resolve_nick(db, full):
    """ Resolve Nick
        If a given full name maps to a nickname in the users database,
        return the nickname. If not, return the full name.
    """
    links = db.execute("SELECT full_name, nickname FROM users")
    for pair in links.fetchall():
        if pair[1] is None: continue
        if pair[0].lower() == full.lower():
            return pair[1]
    return full


def get_users(db):
    """ Get Users
        Get all nicknames from gambit's database and return them as a list
    """
    users = []
    links = db.execute("SELECT nickname FROM users")
    for user in links.fetchall():
        if user[0] is None: continue
        users.append(user[0].lower())
    return users


def get_privilege(db, user, conversation):
    """ Get Privilege
        If a given full name is in the database, return that users
        privilege level
    """
    privileges = db.execute("SELECT full_name, privilege FROM users WHERE conversation_id = ?", (conversation.id_,))
    privileges = privileges.fetchall()
    for privilege in privileges:
        if privilege[0].lower() == user.lower():
            return int(privilege[1])
    return 0
