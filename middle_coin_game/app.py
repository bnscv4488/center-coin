from flask import Flask, render_template, request, send_file
import os
import csv
from io import StringIO, BytesIO
from datetime import datetime

app = Flask(__name__)

players = {}
entry_amount = 5
pool = 0
round_number = 1
history = []
show_results = False
final_results = {}
chart_data = {}
total_entry_spent = 0

def reset_game():
    global players, pool, round_number, history, show_results, final_results, chart_data, total_entry_spent
    players = {}
    pool = 0
    round_number = 1
    history = []
    show_results = False
    final_results = {}
    chart_data = {}
    total_entry_spent = 0

@app.route('/', methods=['GET', 'POST'])
def index():
    global players, entry_amount, pool, round_number, history, show_results, final_results, chart_data, total_entry_spent

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'start':
            player_names = request.form['player_names'].split(',')
            player_names = [name.strip() for name in player_names if name.strip()]
            entry_amount = int(request.form.get('entry_amount', 5))
            players = {name: {'earnings': 0, 'spent': entry_amount} for name in player_names}
            pool = entry_amount * len(players)
            total_entry_spent = pool
            round_number = 1
            history = []
            chart_data = {name: [0] for name in players}
            return render_template('index.html', players=players, entry_amount=entry_amount,
                                   pool=pool, round_number=round_number, show_results=False, final_results={}, chart_data=chart_data, total_entry_spent=total_entry_spent)

        elif action == 'update':
            total_change = 0
            round_record = {'round': round_number, 'results': {}}

            for name in players:
                win = int(request.form.get(f'win_{name}', 0) or 0)
                loss = int(request.form.get(f'loss_{name}', 0) or 0)
                change = win - loss
                total_change += change
                players[name]['earnings'] += change
                round_record['results'][name] = change
                chart_data[name].append(players[name]['earnings'])

            pool -= total_change
            history.append(round_record)

            if pool <= 0:
                round_number += 1
                pool = entry_amount * len(players)  # Reset pool for new round
                total_entry_spent += pool
                for name in players:
                    players[name]['spent'] += entry_amount

            return render_template('index.html', players=players, entry_amount=entry_amount,
                                   pool=pool, round_number=round_number, show_results=False, final_results={}, chart_data=chart_data, total_entry_spent=total_entry_spent)

        elif action == 'download':
            si = StringIO()
            writer = csv.writer(si)
            writer.writerow(["Round", "Player", "Change"])
            for record in history:
                for player, change in record['results'].items():
                    writer.writerow([record['round'], player, change])

            csv_bytes = BytesIO()
            csv_bytes.write(si.getvalue().encode('utf-8'))
            csv_bytes.seek(0)

            filename = f"game_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            return send_file(
                csv_bytes,
                mimetype='text/csv',
                download_name=filename,
                as_attachment=True
            )

        elif action == 'end':
            final_results = {
                name: {
                    'earnings': stats['earnings'],
                    'spent': stats['spent'],
                    'net': stats['earnings'] - stats['spent']
                } for name, stats in players.items()
            }
            net_earnings = sum(stats['earnings'] for stats in players.values())
            show_results = True

            rendered = render_template('index.html', players=players, entry_amount=entry_amount,
                                       pool=pool, round_number=round_number,
                                       show_results=show_results, final_results=final_results,
                                       chart_data=chart_data, total_entry_spent=total_entry_spent, net_earnings=net_earnings)
            reset_game()
            return rendered

    return render_template('index.html', players=players, entry_amount=entry_amount,
                           pool=pool, round_number=round_number, show_results=False, final_results={}, chart_data=chart_data, total_entry_spent=total_entry_spent)

if __name__ == '__main__':
    app.run(debug=True)
