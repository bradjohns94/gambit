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


def update_honorifics(db, conversation_id, threshold=75):
    """ Update Honorifics
        Figure out the karma-based honorifics of each conversation and apply them in the database
        clearing out all other changes
    """
    db.execute("UPDATE users SET title = NULL WHERE title = 'King' OR title = 'Lord'")
    res = db.execute("SELECT target, karma FROM users INNER JOIN karma ON " \
            + "users.nickname = karma.target COLLATE NOCASE " \
            + "WHERE conversation_id = ? AND karma > ? ORDER BY karma DESC", 
            (conversation_id, threshold,))
    ordered = res.fetchall()
    if len(ordered) < 2: return # You're always king of a one-on-one, so forget it
    # First give everyone who has earned their lordship their title
    for user, karma in ordered:
        db.execute("UPDATE users SET title = 'Lord' WHERE nickname = ? " \
                + "AND conversation_id = ?", (user, conversation_id,))
    # Now give the king their rightful crown, but only if they're undisputed
    if ordered[0][1] > ordered[1][1]:
        db.execute("UPDATE users SET title = 'King' WHERE nickname = ? " \
                + "AND conversation_id = ?", (ordered[0][0], conversation_id,))
    db.commit()


def get_honorific_name(db, full_name, conversation_id):
    """ Get Honorific Name
        Given a user's full name determine their associated title (if they have one)
        as well as determine their nickname and return them as their full, honorific
        name
    """
    res = db.execute("SELECT title, nickname FROM users WHERE full_name = ? "
                + "AND conversation_id = ?", (full_name, conversation_id,))
    res = res.fetchone()
    if not res[0]:
        return res[1]
    return res[0] + " " + res[1]
