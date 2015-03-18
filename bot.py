# Heads Up Texas Hold'em Challenge bot
# Based on the Heads Up Omaha Challange - Starter Bot by Jackie <jackie@starapple.nl>
# Last update: 22 May, 2014
# @author Chris Parlette <cparlette@gmail.com> 
# @version 1.0 
# @license MIT License (http://opensource.org/licenses/MIT)

from sys import stderr, stdin, stdout
from poker import Card, Hand, Pocket, Table, Ranker
from itertools import combinations

class Bot(object):
    '''
    Main bot class
    '''
    def __init__(self):
        '''
        Bot constructor

        Add data that needs to be persisted between rounds here.
        '''
        self.settings = {}
        self.match_settings = {}
        self.game_state = {}
        self.pocket = None
        self.bots = {
            'me': {},
            'opponent': {}
        }
        self.ranker = Ranker()

    def run(self):
        '''
        Main loop

        Keeps running while begin fed data from stdin.
        Writes output to stdout, remember to flush.
        '''
        while not stdin.closed:
            try:
                rawline = stdin.readline()

                # End of file check
                if len(rawline) == 0:
                    break

                line = rawline.strip()

                # Empty lines can be ignored
                if len(line) == 0:
                    continue

                parts = line.split()
                command = parts[0].lower()

                if command == 'settings':
                    self.update_settings(parts[1:])
                    pass
                elif command == 'match':
                    self.update_match_info(parts[1:])
                    pass
                elif command.startswith('player'):
                    self.update_game_state(parts[0], parts[1], parts[2])
                    pass
                elif command == 'action':
                    if 'table' not in self.match_settings:
                        stdout.write(self.preflop(parts[2]) + '\n')
                        stdout.flush()
                        pass
                    elif len(self.match_settings['table']) == 10:
                        stdout.write(self.flop(parts[2]) + '\n')
                        stdout.flush()
                        pass
                    elif len(self.match_settings['table']) == 13:
                        stdout.write(self.turn(parts[2]) + '\n')
                        stdout.flush()
                        pass
                    elif len(self.match_settings['table']) == 16:
                        stdout.write(self.river(parts[2]) + '\n')
                        stdout.flush()
                        pass
                else:
                    stderr.write('Unknown command: %s\n' % (command))
                    stderr.flush()
            except EOFError:
                return

    def update_settings(self, options):
        '''
        Updates game settings
        '''
        key, value = options
        self.settings[key] = value

    def update_match_info(self, options):
        '''
        Updates match information
        '''
        key, value = options
        self.match_settings[key] = value

    def update_game_state(self, player, info_type, info_value):
        '''
        Updates game state
        '''
        # Checks if info pertains self
        if player == self.settings['your_bot']:
            
            # Update bot stack
            if info_type == 'stack':
                self.bots['me']['stack'] = int(info_value)

            # Remove blind from stack
            elif info_type == 'post':
                self.bots['me']['stack'] -= int(info_value)

            # Update bot cards
            elif info_type == 'hand':
                self.bots['me']['pocket'] = Pocket(self.parse_cards(info_value))

            # Round winnings, currently unused
            elif info_type == 'wins':
                if 'table' in self.match_settings:
                    del self.match_settings['table']

            else:
                stderr.write('Unknown info_type: %s\n' % (info_type))

        else:

            # Update opponent stack
            if info_type == 'stack':
                self.bots['opponent']['stack'] = int(info_value)

            # Remove blind from opponent stack
            elif info_type == 'post':
                self.bots['opponent']['stack'] -= int(info_value)

            # Opponent hand on showdown, currently unused
            elif info_type == 'hand':
                pass

            # Opponent round winnings, currently unused
            elif info_type == 'wins':
                if 'table' in self.match_settings:
                    del self.match_settings['table']

    def preflop(self, timeout):
        '''
        Handle preflop hand possibilities
        '''
        card1 = self.bots['me']['pocket'].cards[0]
        card2 = self.bots['me']['pocket'].cards[1]

        #pocket pair
        if card1.number == card2.number:
            return 'raise ' + str(int(self.match_settings['max_win_pot']))
        
        #both face cards
        elif card1.number > 8 and card2.number > 8:
            return 'raise ' + str(int(self.match_settings['max_win_pot']))
        
        #suited connectors
        elif card1.suit == card2.suit and abs(card1.number - card2.number) == 1:
            return 'raise ' + str(int(self.match_settings['max_win_pot']))

        #suited ace
        elif card1.suit == card2.suit and (card1.number == 12 or card2.number == 12):
            return 'raise ' + str(int(self.match_settings['max_win_pot']))

        elif int(self.match_settings['amount_to_call']) == 0:
            return 'check 0'
        elif int(self.match_settings['amount_to_call']) < int(self.match_settings['big_blind']):
            return 'call 0'
        else:
            return 'fold 0'

    def flop(self, timeout):
        '''
        Once the flop is out, action is to us
        '''
        card1 = self.bots['me']['pocket'].cards[0]
        card2 = self.bots['me']['pocket'].cards[1]

        available_cards = self.parse_cards(str(self.match_settings['table']))
        available_cards.append(card1)
        available_cards.append(card2)
        ranking = self.ranker.rank_five_cards(available_cards)

        #made hand
        if int(ranking[0]) > 1:
            #already have 2pair or better, bet the pot
            return 'raise ' + str(int(self.match_settings['max_win_pot']))

        #flush draw
        flush_draw = False
        suits = ""
        for card in available_cards:
            suits += card.suit
        for card in available_cards:
            if suits.count(card.suit) > 3:
                flush_draw = True
        if flush_draw:
            return 'raise ' + str(int(self.match_settings['max_win_pot']) / 2)

        #straight draw
        values = sorted(['23456789TJQKA'.find(card.value) for card in available_cards])
        #check cards 0-3
        straight_draw = all(values[i] == values[0] + i for i in range(4))
        #check if we have A-4
        if not straight_draw:
            straight_draw = all(values[i] == values[0] + i for i in range(3)) and values[4] == 12
        #check cards 1-4
        if not straight_draw:
            straight_draw = all(values[i+1] == values[1] + i for i in range(4))
        if straight_draw:
            return 'raise ' + str(int(self.match_settings['max_win_pot']) / 2)

        #pair or ace high
        if int(ranking[0]) == 1 or values[4] == 12:
            if int(self.match_settings['amount_to_call']) < (3 * int(self.match_settings['big_blind'])) and int(self.match_settings['amount_to_call']) > 0:
                return 'call 0'

        if int(self.match_settings['amount_to_call']) == 0:
            return 'check 0'
        else:
            return 'fold 0'


    def turn(self, timeout):
        '''
        Once the turn is out, action is to us
        '''
        card1 = self.bots['me']['pocket'].cards[0]
        card2 = self.bots['me']['pocket'].cards[1]

        available_cards = self.parse_cards(str(self.match_settings['table']))
        available_cards.append(card1)
        available_cards.append(card2)
        ranking = None
        for five_cards in combinations(available_cards, 5):
            if not ranking:
                ranking = self.ranker.rank_five_cards(available_cards)
            else:
                temp_ranking = self.ranker.rank_five_cards(available_cards)
                if int(temp_ranking[0]) > int(ranking[0]):
                    ranking = temp_ranking

        #made hand
        if int(ranking[0]) > 1:
            #already have 2pair or better, bet the pot
            return 'raise ' + str(int(self.match_settings['max_win_pot']))

        #flush draw
        flush_draw = False
        suits = ""
        for card in available_cards:
            suits += card.suit
        for card in available_cards:
            if suits.count(card.suit) > 3:
                flush_draw = True
        if flush_draw:
            return 'call 0'

        #straight draw
        values = sorted(['23456789TJQKA'.find(card.value) for card in available_cards])
        #check cards 0-3
        straight_draw = all(values[i] == values[0] + i for i in range(4))
        #check if we have A-4
        if not straight_draw:
            straight_draw = all(values[i] == values[0] + i for i in range(3)) and values[4] == 12
        #check cards 1-4
        if not straight_draw:
            straight_draw = all(values[i+1] == values[1] + i for i in range(4))
        #check cards 2-5
        if not straight_draw:
            straight_draw = all(values[i+2] == values[2] + i for i in range(4))
        if straight_draw:
            return 'call 0'

        #pair or ace high
        if int(ranking[0]) == 1 or values[4] == 12:
            if int(self.match_settings['amount_to_call']) < (3 * int(self.match_settings['big_blind'])) and int(self.match_settings['amount_to_call']) > 0:
                return 'call 0'

        if int(self.match_settings['amount_to_call']) == 0:
            return 'check 0'
        else:
            return 'fold 0'

    def river(self, timeout):
        '''
        Once the flop is out, action is to us
        '''
        card1 = self.bots['me']['pocket'].cards[0]
        card2 = self.bots['me']['pocket'].cards[1]

        #made hand
        card1 = self.bots['me']['pocket'].cards[0]
        card2 = self.bots['me']['pocket'].cards[1]

        available_cards = self.parse_cards(str(self.match_settings['table']))
        available_cards.append(card1)
        available_cards.append(card2)
        ranking = None
        for five_cards in combinations(available_cards, 5):
            if not ranking:
                ranking = self.ranker.rank_five_cards(available_cards)
            else:
                temp_ranking = self.ranker.rank_five_cards(available_cards)
                if int(temp_ranking[0]) > int(ranking[0]):
                    ranking = temp_ranking

        #made hand
        if int(ranking[0]) > 1:
            #already have 2pair or better, bet the pot
            return 'raise ' + str(int(self.match_settings['max_win_pot']))
        elif int(self.match_settings['amount_to_call']) == 0:
            return 'check 0'
        else:
            return 'fold 0'


    def parse_cards(self, cards_string):
        '''
        Parses string of cards and returns a list of Card objects
        '''
        return [Card(card[1], card[0]) for card in cards_string[1:-1].split(',')]

if __name__ == '__main__':
    '''
    Not used as module, so run
    '''
    Bot().run()