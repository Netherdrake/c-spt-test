import json
import os
import time
import traceback
from pprint import pprint

from piston.steem import BroadcastingError
from steemtools.base import Account, Post
from steemtools.blockchain import Blockchain
from steemtools.node import Node

if os.getenv("UNLOCK", "") == "":
    print("Missing UNLOCK env variable")
    quit()


class AutoVote(object):
    def __init__(self):
        self.steem = Node().default()
        self.my_accounts = [x['name'] for x in self.steem.wallet.getAccounts() if x['type'] == 'posting']

        self.settings = self.load_json('config.json')
        self.author_subscriptions = self.settings['author_subscriptions']
        self.voter_subscriptions = self.settings['voter_subscriptions']
        self.reserve_voting_power = self.settings['reserve_voting_power']

        self._feed_seen_posts = []

    def run(self):
        print("Voting on posts from %d authors." % len(self.author_subscriptions))
        print("Mirroring votes from %d voters." % len(self.voter_subscriptions))
        print("Upvoting from %d accounts: %s" % (len(self.my_accounts), self.my_accounts))

        b = Blockchain()
        for event in b.stream(filter_by=["vote", "comment"], head=True):
            op = event['op']
            op_type = event['op_type']

            # filter out posts we don't care about
            if op_type == "comment":
                if op['author'] not in self.author_subscriptions:
                    continue
            elif op_type == "vote":
                if op['voter'] not in self.voter_subscriptions:
                    continue

            # Sometimes the feed will give duplicates.
            identifier = "@%s/%s" % (op['author'], op['permlink'])
            if identifier in self._feed_seen_posts:
                continue
            self._feed_seen_posts = self._feed_seen_posts[-10000:] + [identifier]

            # fetch the post
            p = Post(identifier)

            # we only care about main posts
            if p.is_comment():
                continue

            # filter out test and nsfw posts
            if p.contains_tags(filter_by=['spam', 'test', 'nsfw']):
                continue

            print("\n===> New post by @%s %s" % (p.author, p.get_url()))
            print(time.ctime())
            print(p.get_url())
            self.upvote_from_all_accounts(identifier)

    def upvote_from_all_accounts(self, identifier):
        post = Post(identifier)
        minutes_elapsed = post.time_elapsed() / 60
        print("Time elapsed: %.2f min, Current Payout: $%.2f" % (minutes_elapsed, post.payout()))

        for account in self.my_accounts:
            voting_power = int(str(self.steem.rpc.get_account(account)['voting_power'])[:2])

            if voting_power < self.reserve_voting_power:
                print("@%s has low voting power. Skipping.." % account)
                continue

            if account == post['author']:
                print("====> @%s is the author of the post. Skipping..." % account)
                continue

            if Account(account).check_if_already_voted(post):
                print("====> @%s had already voted on this post. Skipping..." % account)
                continue

            try:
                if not self.settings['sim_mode']:
                    post.vote(100, account)
                print("====> Upvoted as %s" % account)
            except BroadcastingError as e:
                print("ERROR: Upvoting with %s failed." % account, str(e))

    @staticmethod
    def load_json(filename):
        with open(filename) as data_file:
            data = json.load(data_file)

        return data


if __name__ == "__main__":
    print("Starting...")
    while True:
        try:
            av = AutoVote()
            av.run()
        except (KeyboardInterrupt, SystemExit):
            quit("Quitting!")
        except:
            pprint(traceback.format_exc())
            print("Restarting...")
            continue
