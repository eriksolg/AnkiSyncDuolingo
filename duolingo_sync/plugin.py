# import the main window object (mw) from aqt
from aqt import mw
# import the "show info" tool from utils.py
from aqt.utils import showInfo, getText, askUser
# import all of the Qt GUI library
from aqt.qt import *

from anki.lang import _
from anki.utils import splitFields

from lib import duolingo


def getDuolingoModel():

    m = mw.col.models.byName("Duolingo Sync")

    if not m:
        if askUser("Duolingo Sync note type not found. Create?"):

            mm = mw.col.models
            m = mm.new(_("Duolingo Sync"))

            for fieldName in ["Gid", "Gender", "Source", "Target"]:
                fm = mm.newField(_(fieldName))
                mm.addField(m, fm)

            t = mm.newTemplate(_("Card 1"))
            t['qfmt'] = "{{" + _("Source") + "}}"
            t['afmt'] = "{{FrontSide}}\n\n<hr id=answer>\n\n" + "{{" + _("Target") + "}}"
            mm.addTemplate(m, t)
            mm.add(m)

            mw.col.models.save(m)

    return m


def getDuolingoDeck():
    d = mw.col.decks.byName("Duolingo")

    if not d:
        if askUser("Duolingo deck not found. Create?"):
            mw.col.decks.id("Duolingo", create=True)

    d = mw.col.decks.byName("Duolingo")
    return d


def testFunction():

    model = getDuolingoModel()
    deck = getDuolingoDeck()

    notes = mw.col.db.list("select flds from notes where mid = ?", model['id'])
    duolingo_gids = [splitFields(note)[0] for note in notes]

    username = getText("Your Duolingo username:")[0]

    if username:
        password = getText("Your Duolingo password:")[0]

        if password:
            lingo = duolingo.Duolingo(username, password=password)
            response = lingo.get_vocabulary()
            language_string = response['language_string']
            vocabs = response['vocab_overview']

            did = mw.col.decks.id("Duolingo")
            mw.col.decks.select(did)

            m = mw.col.models.byName("Duolingo Sync")
            deck = mw.col.decks.get(did)
            deck['mid'] = m['id']
            mw.col.decks.save(deck)

            words_to_add = []
            for vocab in vocabs:

                if vocab['id'] not in duolingo_gids:
                    words_to_add.append(vocab)

            if askUser("Add {} cards?".format(len(words_to_add))):

                word_chunks = [words_to_add[x:x + 50] for x in xrange(0, len(words_to_add), 50)]

                for word_chunk in word_chunks:
                    translations = lingo.get_translations([vocab['word_string'] for vocab in word_chunk])

                    for vocab in word_chunk:
                        n = mw.col.newNote()

                        n['Gid'] = vocab['id']
                        n['Gender'] = vocab['gender'] if vocab['gender'] else ''
                        n['Source'] = '; '.join(translations[vocab['word_string']])
                        n['Target'] = vocab['word_string']

                        n.addTag(language_string)

                        if vocab['pos']:
                            n.addTag(vocab['pos'])

                        if vocab['skill']:
                            n.addTag(vocab['skill'])

                        mw.col.addNote(n)

# create a new menu item, "test"
action = QAction("Sync Duolingo", mw)
# set it to call testFunction when it's clicked
action.triggered.connect(testFunction)
# and add it to the tools menu
mw.form.menuTools.addAction(action)


