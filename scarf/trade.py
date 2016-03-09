from scarf import app
from flask import flash, render_template, session, request, redirect
from scarflib import PageData, NoItem, NoUser, SiteUser, SiteItem, redirect_back, item_by_uid, user_by_uid, send_pm, add_tradeitem, PrivateMessage, TradeMessage, messagestatus, TradeItem, tradeitemstatus, deobfuscate, obfuscate
from main import page_not_found

# fix these URLs s/pm/trade/
@app.route('/user/<username>/pm/<messageid>/<action>/<item>')
@app.route('/user/<username>/pm/<messageid>/<action>')
def accepttradeitem(username, messageid, action, item=None):
    pd = PageData()

    if not pd.authuser.username == username:
        return page_not_found(404)

    if 'username' in session:
        if item:
            try:
                ti = TradeItem(item)
            except:
                return page_not_found(404)

            if action == "accept":
                ti.accept()
            elif action == "reject":
                ti.reject()
            else:
                return page_not_found(404)
        else:
            try:
                t = TradeMessage.create(deobfuscate(messageid))
            except NoItem:
                return page_not_found(404)

            if action == "settle":
                t.settle()
            elif action == "cancel":
                t.cancel()
            elif action == "reject":
                t.reject()
            elif action == "reopen":
                t.unread()
                t.read()
            else:
                return page_not_found(404)

    return redirect_back('index')

@app.route('/user/<username>/trade/<itemid>/debug', methods=['GET'], defaults={'debug': True})
@app.route('/user/<username>/trade/<itemid>', methods=['GET', 'POST'], defaults={'debug': False})
def trade(username, itemid, debug):
    pd = PageData()

    try:
        pd.tradeuser = SiteUser.create(username)
    except (NoItem, NoUser):
        return page_not_found(404)

    if 'username' in session:
        if request.method == 'POST':
            items = request.form.getlist('item')
            message = request.form['body']
            subject = request.form['subject']

            try:
                parent = request.form['parent']
            except:
                parent = None

            if message and subject:
                messageid = send_pm(pd.authuser.uid, pd.tradeuser.uid, subject, message, messagestatus['unread_trade'], parent)

                for item in items:
                    add_tradeitem(item, messageid, pd.authuser.uid, tradeitemstatus['accepted'])

                add_tradeitem(SiteItem(itemid).uid, messageid, pd.tradeuser.uid, tradeitemstatus['unmarked'])

                if messageid:
                    flash('Submitted trade request!')
                    return redirect('/user/' + pd.authuser.username + '/pm/' + obfuscate(messageid))

            return redirect('/item/' + itemid)

    pd.title = "Trade for " + itemid

    try:
        pd.authuser.ownwant = pd.authuser.query_collection(itemid)
    except AttributeError:
        pass

    try:
        pd.tradeuser.ownwant = pd.tradeuser.query_collection(itemid)
        pd.item = SiteItem(itemid)
    except (NoItem, NoUser):
        return page_not_found(404)

    if debug:
        if 'username' in session and pd.authuser.accesslevel == 255:
            pd.debug = dbg(pd)

    return render_template('trade.html', pd=pd)
