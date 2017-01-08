from app import app
from app.models import *
from flask import render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import func
from sqlalchemy.sql import label
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
import time, os
from datetime import datetime
from werkzeug import secure_filename

login_manager = LoginManager()
login_manager.init_app(app)
bcrypt = Bcrypt(app)
login_manager.login_view = "login"

@app.route("/login", methods=["GET", "POST"])
def login():
	if request.method == 'GET':
		return render_template('login.html')
	elif request.method == 'POST':
		form_username = request.json['username']
		form_password = request.json['password']
		user = User.query.filter_by(username = form_username).first()
		if user:
			if bcrypt.check_password_hash(user.password, form_password):
				user.authenticated = True
				login_user(user)
				return jsonify(status="success")
		return jsonify(status="error", text='Usuário ou senha incorretos.')

@app.route("/logout", methods=["GET"])
def logout():
	user = current_user
	user.authenticated = False
	logout_user()
	return redirect('login')


@app.route('/')
def root():
	return redirect(url_for('index'))

@app.route('/index')
@login_required
def index():
    accounts = Account.query.filter_by(user_id = current_user.id, type = '1', is_active = 'S').order_by(Account.name.asc()).all()
    return render_template('index.html', accounts = accounts)


@app.route('/widgets/credit_cards_overview')
@login_required
def widgets_credit_cards_overview():
        credit_cards_info = list()
        credit_cards = Account.query.filter_by(user_id = current_user.id, type = '2', is_active = 'S').order_by(Account.name.asc()).all()
        for credit_card in credit_cards:
                expenses = 0.00
                for credit_card_transaction in CreditCardTransaction.query.filter_by(user_id = current_user.id, credit_card_id = credit_card.id, type = 'DEB', is_done = 'S', payment_done = 'N').all():
                        expenses += credit_card_transaction.amount
                credit_cards_info.append({'id': credit_card.id, 'name': credit_card.name, 'limit': credit_card.credit_card_limit, 'limit_left': credit_card.credit_card_limit - expenses})
        return render_template('widgets_credit_cards_overview.html', credit_cards = credit_cards_info)

@app.route('/accounts/<id>/balance')
@login_required
def get_account_balance(id):
        if request.method == 'GET':
                incomes = 0.00
                expenses = 0.00
                balance = 0.00
                account_name = Account.query.filter_by(user_id = current_user.id, id = id).first().name

                for transaction in Transaction.query.filter_by(user_id = current_user.id, account_id = id, type = 'CRE', is_done = 'S').all():
                        incomes += transaction.amount
                for transaction in Transaction.query.filter_by(user_id = current_user.id, account_id = id, type = 'DEB', is_done = 'S').all():
                        expenses += transaction.amount
                balance = incomes - expenses
                return jsonify({'name': account_name, 'balance': balance})

@app.route('/accounts/total_balance_until_date/<date>', methods=['GET'])
@login_required
def get_accounts_total_balance_until_date(date):
        if request.method == 'GET':
                total_of_incomes = 0
                total_of_expenses = 0

                for transaction in Transaction.query.filter_by(user_id = current_user.id).filter_by(type = 'CRE').filter(Transaction.transaction_date <= datetime.strptime(date,'%Y-%m-%d').date()).all():
                        account_type = Account.query.filter_by(id = transaction.account_id).first().type
                        if account_type == '1':
                                total_of_incomes += transaction.amount

                for transaction in Transaction.query.filter_by(user_id = current_user.id).filter_by(type = 'DEB').filter(Transaction.transaction_date <= datetime.strptime(date,'%Y-%m-%d').date()).all():
                        account_type = Account.query.filter_by(id = transaction.account_id).first().type
                        if account_type == '1':
                                total_of_expenses += transaction.amount
                balance = total_of_incomes - total_of_expenses
                return str(balance)


@app.route('/transactions/<start_date>/<end_date>/json', methods=['GET'])
@login_required
def get_transactions_by_date_json(start_date, end_date):
        if request.method == 'GET':
                transactions = [dict(
                        id = transaction.id,
                        description = transaction.description,
                        amount = transaction.amount,
                        transaction_date = str(transaction.transaction_date),
                        account_id = transaction.account_id,
                        account_name = Account.query.filter_by(id = transaction.account_id).filter_by(user_id = current_user.id).first().name,
                        account_type = Account.query.filter_by(id = transaction.account_id).filter_by(user_id = current_user.id).first().type,
                        category_id = transaction.category_id,
                        category_name = Category.query.filter_by(id = transaction.category_id).filter_by(user_id = current_user.id).first().name,
                        type = transaction.type,
                        is_done = transaction.is_done,
                        attachment_filename = transaction.attachment_filename
                               ) for transaction in Transaction.query.filter_by(user_id = current_user.id).filter(Transaction.transaction_date >= datetime.strptime(start_date,'%Y-%m-%d').date()).filter(Transaction.transaction_date <= datetime.strptime(end_date,'%Y-%m-%d').date()).order_by(Transaction.transaction_date.asc()).all()]
                return jsonify(transactions=transactions)


@app.route('/credit_cards_transactions/<id>/<start_date>/<end_date>/json', methods=['GET'])
@login_required
def get_credit_cards_transactions_by_date_json(id, start_date, end_date):
        if request.method == 'GET':
                transactions = [dict(
                        id = transaction.id,
                        description = transaction.description,
                        amount = transaction.amount,
                        transaction_date = str(transaction.transaction_date),
                        invoice_date = str(transaction.invoice_date),
                        credit_card_id = transaction.credit_card_id,
                        credit_card_name = Account.query.filter_by(id = transaction.credit_card_id).filter_by(user_id = current_user.id).first().name,
                        type = transaction.type,
                        is_done = transaction.is_done,
                        payment_done = transaction.payment_done
                               ) for transaction in CreditCardTransaction.query.filter_by(user_id = current_user.id).filter(CreditCardTransaction.invoice_date >= datetime.strptime(start_date,'%Y-%m-%d').date()).filter(CreditCardTransaction.invoice_date <= datetime.strptime(end_date,'%Y-%m-%d').date()).filter_by(credit_card_id = id).order_by(CreditCardTransaction.transaction_date.asc()).all()]
                return jsonify(transactions=transactions)

@app.route('/categories',methods=['GET','POST'])
@login_required
def list_categories():
	if request.method == 'GET':
		return render_template('categories.html', categories = Category.query.filter_by(user_id = current_user.id).order_by(Category.name.asc()).all())

@app.route('/categories/new',methods=['GET','POST'])
@login_required
def new_category():
	if request.method == 'GET':
		return render_template('create_category.html')
	elif request.method == 'POST':
		form_category_name = request.form['name']
		if form_category_name == '':
			flash('Não é possível adicionar a categoria','error')
			return redirect(url_for('list_categories'))
		db.session.add(Category(None,form_category_name,current_user.id))
		db.session.commit()
		flash('Categoria adicionada','success')
		return redirect(url_for('list_categories'))

@app.route('/categories/edit/<id>',methods=['GET','POST'])
@login_required
def edit_category(id):
        if request.method == 'GET':
                category = Category.query.filter_by(id = id).first()
                return render_template('edit_category.html', category=category)
        elif request.method == 'POST':
                form_category_name = request.form['name']
                if form_category_name == '':
                        flash('Não foi possivel editar a categoria', 'error')
                        return redirect(url_for('list_categories'))
                category = Category.query.filter_by(id = id).first()
                category.name = request.form['name']
                db.session.commit()
                flash('Categoria atualizada','success')
                return redirect(url_for('list_categories'))

@app.route('/categories/delete/<id>')
@login_required
def delete_category(id):
        if Transaction.query.filter_by(user_id = current_user.id).filter_by(category_id = id).first() is not None:
                flash('Não é possível deletar a categoria pois existem lançamentos associados a ela', 'error')
                return redirect(url_for('list_categories'))
        db.session.delete(Category.query.filter_by(user_id = current_user.id).filter_by(id = id).first())
        db.session.commit()
        flash('Categoria deletada', 'success')
        return redirect(url_for('list_categories'))


@app.route('/accounts',methods=['GET','POST'])
@login_required
def list_accounts():
        if request.method == 'GET':
                accounts = Account.query.filter_by(type = '1').filter_by(user_id = current_user.id).order_by(Account.name.asc()).all()
                return render_template('accounts.html',accounts=accounts)

@app.route('/accounts/new',methods=['GET','POST'])
@login_required
def new_account():
        if request.method == 'GET':
                return render_template('create_account.html')
        elif request.method == 'POST':
                form_account_name = request.form['name']
                form_account_is_active = True if request.form.get('is_active') is None else False
                if form_account_name == '':
                        flash('Não foi possivel adicionar a conta', 'error')
                        return redirect(url_for('list_accounts'))
                db.session.add(Account(None, form_account_name, '1', None, 'S' if form_account_is_active is True else 'N', current_user.id))
                db.session.commit()
                flash('Conta adicionada', 'success')
                return redirect(url_for('list_accounts'))

@app.route('/accounts/edit/<id>', methods=['GET','POST'])
@login_required
def edit_account(id):
        if request.method == 'GET':
                account = Account.query.filter_by(id = id).first()
                return render_template('edit_account.html', account=account)
        elif request.method == 'POST':
                form_account_name = request.form['name']
                form_account_is_active = True if request.form.get('is_active') is None else False
                if form_account_name == '':
                        flash('Não foi possivel alterar a conta')
                        return redirect(url_for('list_accounts'))
                account = Account.query.filter_by(id = id).first()
                account.name = form_account_name
                account.is_active = 'S' if form_account_is_active is True else 'N'
                db.session.commit()
                flash('Conta atualizada')
                return redirect(url_for('list_accounts'))

@app.route('/accounts/delete/<id>')
@login_required
def delete_account(id):
        if Transaction.query.filter_by(user_id = current_user.id).filter_by(account_id = id).first() is not None:
                flash('Não é possível deletar a conta pois existem lançamentos associados a ela', 'error')
                return redirect(url_for('list_accounts'))
        db.session.delete(Account.query.filter_by(user_id = current_user.id).filter_by(id = id).first())
        db.session.commit()
        flash('Conta deletada', 'success')
        return redirect(url_for('list_accounts'))

@app.route('/credit_cards', methods=['GET','POST'])
@login_required
def list_credit_cards():
        if request.method == 'GET':
                credit_cards = Account.query.filter_by(type = '2').filter_by(user_id = current_user.id).all()
                return render_template('credit_cards.html', credit_cards=credit_cards)

@app.route('/credit_cards/new', methods=['GET', 'POST'])
@login_required
def new_credit_card():
        if request.method == 'GET':
                return render_template('create_credit_card.html')
        elif request.method == 'POST':
                form_credit_card_name = request.form['name']
                form_credit_card_limit = request.form['limit']
                form_credit_card_is_active = True if request.form.get('is_active') is None else False
                if form_credit_card_name == '':
                        flash('Não foi possivel adicionar o cartão', 'error')
                        return redirect(url_for('list_credit_cards'))
                db.session.add(Account(None, form_credit_card_name, '2', (form_credit_card_limit).replace(',','.'), 'S' if form_credit_card_is_active is True else 'N', current_user.id))
                db.session.commit()
                flash('Cartão adicionado', 'success')
                return redirect(url_for('list_credit_cards'))


@app.route('/credit_cards/edit/<id>', methods = ['GET','POST'])
@login_required
def edit_credit_card(id):
        if request.method == 'GET':
                credit_card = Account.query.filter_by(id = id).first()
                return render_template('edit_credit_card.html', credit_card = credit_card)
        if request.method == 'POST':
                form_credit_card_name = request.form['name']
                form_credit_card_limit = request.form['limit']
                form_credit_card_is_active = True if request.form.get('is_active') is None else False
                if form_credit_card_name == '':
                        flash('Não foi possivel editar o cartão', 'error')
                        return redirect(url_for('list_credit_cards'))
                credit_card = Account.query.filter_by(id = id).first()
                credit_card.name = form_credit_card_name
                credit_card.credit_card_limit = (form_credit_card_limit).replace(',','.')
                credit_card.is_active = 'S' if form_credit_card_is_active is True else 'N'
                db.session.commit()
                flash('Cartão atualizado')
                return redirect(url_for('list_credit_cards'))

@app.route('/credit_cards/delete/<id>')
@login_required
def delete_credit_card(id):
        if Transaction.query.filter_by(user_id = current_user.id).filter_by(account_id = id).first() is not None:
                flash('Não é possível deletar o cartão de crédito pois existem lançamentos associados a ele', 'error')
                return redirect(url_for('list_credit_cards'))
        db.session.delete(Account.query.filter_by(user_id = current_user.id).filter_by(id = id).first())
        db.session.commit()
        flash('Cartão de crédito deletado', 'success')
        return redirect(url_for('list_credit_cards'))

@app.route('/credit_cards/<id>/invoices')
@login_required
def list_credit_card_invoices(id):
        if request.method == 'GET':
                credit_card = Account.query.filter_by(user_id = current_user.id).filter_by(id = id).first()
                return render_template('credit_card_invoices.html', credit_card = credit_card)

@app.route('/credit_cards/<id>/invoices/transactions/new', methods = ['GET','POST'])
@login_required
def new_credit_card_transaction(id):
        if request.method == 'GET':
                credit_card = Account.query.filter_by(user_id = current_user.id).filter_by(id = id).first()
                return render_template('create_credit_card_transaction.html', credit_card = credit_card)
        elif request.method == 'POST':
                form_credit_card_transaction_description = request.form['description']
                form_credit_card_transaction_amount = request.form['amount'] or 0.00
                form_credit_card_transaction_transaction_date = datetime.strptime(request.form['transaction_date'],'%d/%m/%Y').date()
                form_credit_card_transaction_invoice_date = datetime.strptime(request.form['invoice_date'],'%d/%m/%Y').date()
                form_credit_card_transaction_type = request.form['type']
                form_credit_card_transaction_is_done = 'S' if request.form.get('is_done') is not None else 'N'
                form_credit_card_transaction_payment_done = 'S' if request.form.get('payment_done') is not None else 'N'
                credit_card_transaction_user_id = current_user.id

                db.session.add(CreditCardTransaction(None, form_credit_card_transaction_description, (form_credit_card_transaction_amount).replace(',','.'), form_credit_card_transaction_transaction_date, form_credit_card_transaction_invoice_date, id, form_credit_card_transaction_type, form_credit_card_transaction_is_done, form_credit_card_transaction_payment_done, credit_card_transaction_user_id))
                db.session.commit()
                flash('Lançamento adicionado', 'success')
                return redirect(url_for('list_credit_card_invoices', id = id))


@app.route('/credit_cards/<id>/invoices/transactions/edit/<transaction_id>', methods = ['GET','POST'])
@login_required
def edit_credit_card_transaction(id, transaction_id):
        if request.method == 'GET':
                credit_card = Account.query.filter_by(user_id = current_user.id).filter_by(id = id).first()
                credit_card_transaction = CreditCardTransaction.query.filter_by(user_id = current_user.id).filter_by(id = transaction_id).first()
                return render_template('edit_credit_card_transaction.html', credit_card = credit_card, credit_card_transaction = credit_card_transaction)
        elif request.method == 'POST':
                form_credit_card_transaction_description = request.form['description']
                form_credit_card_transaction_amount = request.form['amount'] or 0.00
                form_credit_card_transaction_transaction_date = datetime.strptime(request.form['transaction_date'],'%d/%m/%Y').date()
                form_credit_card_transaction_invoice_date = datetime.strptime(request.form['invoice_date'],'%d/%m/%Y').date()
                form_credit_card_transaction_type = request.form['type']
                form_credit_card_transaction_is_done = 'S' if request.form.get('is_done') is not None else 'N'
                form_credit_card_transaction_payment_done = 'S' if request.form.get('payment_done') is not None else 'N'

                credit_card_transaction = CreditCardTransaction.query.filter_by(user_id = current_user.id).filter_by(id = transaction_id).first()
                credit_card_transaction.description = form_credit_card_transaction_description = request.form['description']
                credit_card_transaction.amount = (form_credit_card_transaction_amount).replace(',','.')
                credit_card_transaction.transaction_date = form_credit_card_transaction_transaction_date
                credit_card_transaction.invoice_date = form_credit_card_transaction_invoice_date
                credit_card_transaction.type = form_credit_card_transaction_type
                credit_card_transaction.is_done = form_credit_card_transaction_is_done
                credit_card_transaction.payment_done = form_credit_card_transaction_payment_done
                db.session.commit()
                flash('Lançamento editado', 'success')
                return redirect(url_for('list_credit_card_invoices', id = id))

@app.route('/credit_cards/<id>/invoices/transactions/delete/<transaction_id>')
@login_required
def delete_credit_card_transaction(id, transaction_id):
        db.session.delete(CreditCardTransaction.query.filter_by(user_id = current_user.id).filter_by(id = transaction_id).first())
        db.session.commit()
        flash('Lançamento deletado')
        return redirect(url_for('list_credit_card_invoices', id = id))

@app.route('/transactions')
@login_required
def list_transactions():
        if request.method == 'GET':
                return render_template('transactions.html')

@app.route('/transactions/new', methods=['GET','POST'])
@login_required
def new_transaction():
        if request.method == 'GET':
                accounts = Account.query.filter_by(user_id = current_user.id).filter_by(is_active = 'S').order_by(Account.name.asc()).all()
                categories = Category.query.filter_by(user_id = current_user.id).order_by(Category.name.asc()).all()
                return render_template('create_transaction.html', accounts=accounts, categories=categories)
        elif request.method == 'POST':
                form_transaction_description = request.form['description']
                form_transaction_amount = request.form['amount'] or 0.00
                form_transaction_transaction_date = datetime.strptime(request.form['transaction_date'],'%d/%m/%Y').date()
                form_transaction_account_id = request.form['account']
                form_transaction_category_id = request.form['category']
                form_transaction_type = request.form['type']
                form_transaction_is_done = 'S' if request.form.get('is_done') is not None else 'N'
                form_transaction_attachment_filename = request.files['attachment_filename']
                transaction_user_id = current_user.id

                if not form_transaction_attachment_filename.filename == '':
                        attachment_filename = secure_filename((form_transaction_attachment_filename.filename).split('.')[0]) + '-' + str(int(time.time())) + '-' + str(current_user.id) + '.' + form_transaction_attachment_filename.filename.rsplit('.', 1)[1]
                        form_transaction_attachment_filename.save(os.path.join(app.config['UPLOAD_FOLDER'], attachment_filename))

                else:
                        attachment_filename = None

                db.session.add(Transaction(None, form_transaction_description, (form_transaction_amount).replace(',','.'), form_transaction_transaction_date, form_transaction_account_id, form_transaction_category_id, form_transaction_type, form_transaction_is_done, attachment_filename, transaction_user_id))
                db.session.commit()

                flash('Lançamento adicionado', 'success')
                return redirect(url_for('list_transactions'))


@app.route('/transactions/edit/<id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
        if request.method == 'GET':
                transaction = Transaction.query.filter_by(user_id = current_user.id).filter_by(id = id).first()
                accounts = Account.query.filter_by(user_id = current_user.id).order_by(Account.name.asc()).all()
                categories = Category.query.filter_by(user_id = current_user.id).order_by(Category.name.asc()).all()
                return render_template('edit_transaction.html', transaction=transaction, accounts=accounts, categories=categories)
        elif request.method == 'POST':
                form_transaction_description = request.form['description']
                form_transaction_amount = request.form['amount'] or 0.00
                form_transaction_transaction_date = datetime.strptime(request.form['transaction_date'],'%d/%m/%Y').date()
                form_transaction_account_id = request.form['account']
                form_transaction_category_id = request.form['category']
                form_transaction_type = request.form['type']
                form_transaction_is_done = 'S' if request.form.get('is_done') is not None else 'N'
                form_transaction_attachment_filename = request.files['attachment_filename']
                transaction_user_id = current_user.id

                transaction = Transaction.query.filter_by(user_id = current_user.id).filter_by(id = id).first()
                if not form_transaction_attachment_filename.filename == '':
                        attachment_filename = secure_filename((form_transaction_attachment_filename.filename).split('.')[0]) + '-' + str(int(time.time())) + '-' + str(current_user.id) + '.' + form_transaction_attachment_filename.filename.rsplit('.', 1)[1]
                        form_transaction_attachment_filename.save(os.path.join(app.config['UPLOAD_FOLDER'], attachment_filename))
                else:
                        if transaction.attachment_filename == None:
                            attachment_filename = None
                        else:
                            attachment_filename = transaction.attachment_filename

                transaction.description = form_transaction_description
                transaction.amount = (form_transaction_amount).replace(',','.')
                transaction.transaction_date = datetime.strptime(request.form['transaction_date'],'%d/%m/%Y').date()
                transaction.account_id = form_transaction_account_id
                transaction.category_id = form_transaction_category_id
                transaction.type = form_transaction_type
                transaction.is_done = form_transaction_is_done
                transaction.attachment_filename = attachment_filename

                db.session.commit()
                flash('Lançamento editado', 'success')
                return redirect(url_for('list_transactions'))

@app.route('/transactions/delete/<id>')
@login_required
def delete_transaction(id):
        if request.method == 'GET':
                db.session.delete(Transaction.query.filter_by(user_id = current_user.id).filter_by(id = id).first())
                db.session.commit()
                flash('Lançamento deletado', 'sucess')
                return redirect(url_for('list_transactions'))

@app.route('/transfers/new', methods = ['GET', 'POST'])
@login_required
def new_transfer():
        if request.method == 'GET':
                accounts = Account.query.filter_by(user_id = current_user.id).filter_by(is_active = 'S').filter_by(type = '1').order_by(Account.name.asc()).all()
                return render_template('create_transfer.html', accounts=accounts)
        elif request.method == 'POST':
                form_transfer_src_account = request.form['src-account']
                form_transfer_dst_account = request.form['dst-account']
                form_transfer_transaction_date = datetime.strptime(request.form['transaction_date'],'%d/%m/%Y').date()
                form_transfer_description = request.form['description']
                form_transfer_amount = request.form['amount'] or 0.00
                transfer_category_id = Category.query.filter_by(user_id = current_user.id).filter_by(name = 'Transferência').first().id
                if form_transfer_src_account == form_transfer_dst_account:
                        flash('Não é possivel transferir pois a conta de origem e destino é a mesma', 'error')
                        return redirect(url_for('list_transactions'))
                transaction_debit = Transaction(None, form_transfer_description, (form_transfer_amount).replace(',','.'), form_transfer_transaction_date, form_transfer_src_account, transfer_category_id, 'DEB', 'S', None, current_user.id)
                transaction_credit = Transaction(None, form_transfer_description, (form_transfer_amount).replace(',','.'), form_transfer_transaction_date, form_transfer_dst_account, transfer_category_id, 'CRE', 'S', None, current_user.id)
                db.session.add(transaction_debit)
                db.session.add(transaction_credit)
                db.session.commit()
                flash('Transferência adicionada', 'success')
                return redirect(url_for('list_transactions'))

@app.route('/reports/<id>', methods=['GET','POST'])
@login_required
def generate_report(id):
        if id == '1':
                if request.method == 'GET':
                        return render_template('report_01.html')
                elif request.method == 'POST':
                        start_date = datetime.strptime(request.json['start_date'],'%Y-%m-%d').date()
                        end_date = datetime.strptime(request.json['end_date'],'%Y-%m-%d').date()
                        total_incomes_expenses_amount_by_category = []
                        categories = Category.query.filter_by(user_id = current_user.id).order_by(Category.name.asc()).filter(~Category.name.contains('%Transferência%')).all()
                        for category in categories:
                                incomes = db.session.query(func.sum(Transaction.amount).label('total_incomes')).filter_by(user_id = current_user.id, category_id = category.id, type = 'CRE', is_done = 'S').filter(Transaction.transaction_date.between(start_date, end_date)).first()
                                expenses = db.session.query(func.sum(Transaction.amount).label('total_expenses')).filter_by(user_id = current_user.id, category_id = category.id, type = 'DEB', is_done = 'S').filter(Transaction.transaction_date.between(start_date, end_date)).first()
                                total_incomes_expenses_amount_by_category.append({'category_id': category.id, 'name': category.name, 'incomes': 0.00 if incomes.total_incomes is None else float(incomes.total_incomes), 'expenses': 0.00 if expenses.total_expenses is None else float(expenses.total_expenses)})

                        return jsonify(total_incomes_expenses_amount_by_category = total_incomes_expenses_amount_by_category)
