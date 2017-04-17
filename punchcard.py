#!/usr/bin/env python

import sys
import argparse
from subprocess import check_output
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# dependencies
from iso8601 import parse_date
from tzlocal import get_localzone
import matplotlib.pyplot as plt

# knobs
CIRCLE_SCALE = 1250
HEIGHT_SCALE = 0.8
WIDTH_SCALE  = 1.1
LABEL_SIZE = 24

AUTHORS_SINCE = get_localzone().localize(datetime.now()) - timedelta(days=365)
"""
Only map authors who have committed since this date.
"""


MIN_COMMITS = 5
"""
Minimum number of commits for an author to be considered.
"""

def _gen_plot(xs, ys, ss, names):
    """
    Horrible code that generates the scatter plot and writes it to hard-coded
    file "out.png".

    Args:
        xs (list)
        ys (list)
        ss (list)
        names (list)

    Returns
        None
    """
    fig = plt.figure(figsize=(WIDTH_SCALE * 24,
                              HEIGHT_SCALE * len(names)),
                     facecolor='#efefef')
    plt.scatter(xs, ys, s=ss, c='#333333', edgecolor='#333333')
    ax = plt.gca()
    ax.set_frame_on(False)

    ax.set_yticks(range(len(names)))
    for tx in ax.set_yticklabels(names):
        tx.set_color('#555555')
        tx.set_size(LABEL_SIZE)
    plt.ylim((-1, len(names) + 1))

    ax.set_xticks(range(24))
    ts = '12am 1 2 3 4 5 6 7 8 9 10 11 12pm 1 2 3 4 5 6 7 8 9 10 11'.split(' ')
    for tx in ax.set_xticklabels(ts):
        tx.set_color('#555555')
        tx.set_size(LABEL_SIZE)

    ax.set_aspect('equal')
    fig.savefig("out.png")

def _add_commit_to_counts(commit_counts, (name, dt)):
    """
    Args
        commit_counts (dict)
        name (str)
        timestamp (str): iso8601

    Returns
        dict
    """
    commit_counts[name][dt.hour] += 1
    return commit_counts

def _normalize_counts(counts):
    """
    Normalize the counts on a per-user basis so everyone takes up about the same
    amount of volume on the graph.

    Args
        counts (dict)

    Returns
        dict
    """
    for name, counts_by_hour in counts.items():
        total = sum(counts_by_hour.values())
        for hour, commit_count in counts_by_hour.items():
            counts[name][hour] = (CIRCLE_SCALE * commit_count) / float(total)
    return counts

def _parse_timestamp((name, timestamp)):
    """
    Args
        (author (str), timestamp (str))

    Returns
        (str, datetime.datetime)
    """
    dt = parse_date(timestamp).astimezone(get_localzone())
    return name, dt

def _sanitize_author((author, timestamp)):
    """
    Some bullshit attempt to sanitize the author string which varies between
    peoples machines.

    Args:
        (author (str), timestamp (str))

    Returns:
        (str, str)
    """
    return author.lower(), timestamp

def _filter_old_authors(commits):
    newest_commits = {}
    for author, dt in commits:
        cur_newest = newest_commits.get(author)
        if not cur_newest or cur_newest < dt:
            newest_commits[author] = dt
    relevant_authors = {author for author, dt in newest_commits.iteritems()
                        if dt > AUTHORS_SINCE}
    commits = [(author, dt) for author, dt in commits
               if author in relevant_authors]
    return commits

def _filter_low_contributing_authors(commits):
    """
    Args:
        commits (list)

    Returns:
        list
    """
    counts = Counter([author for author, _ in commits])
    return [(author, dt) for author, dt in commits
            if counts[author] > MIN_COMMITS]

def _get_counts(git_dir):
    """
    Args:
        git_dir (str)

    Returns:
        dict
    """
    command = ['git', '--git-dir', git_dir, 'log', '--pretty=format:%aN|%aI']
    commits = [line.split('|') for line in check_output(command).splitlines()]
    commits = map(_parse_timestamp, commits)
    commits = map(_sanitize_author, commits)
    commits = _filter_old_authors(commits)
    commits = _filter_low_contributing_authors(commits)
    counts = reduce(_add_commit_to_counts,
                    commits,
                    defaultdict(lambda: defaultdict(int)))
    return counts

def _create_seqs(counts):
    """
    Args:
        counts (dict)

    Returns:
        (list, list, list, list)
    """
    sorted_names = sorted(counts.keys())
    name_indices = dict(zip(sorted_names, range(len(counts))))
    xs = []
    ys = []
    ss = []
    for name, counts_by_hour in counts.iteritems():
        for hour, count in counts_by_hour.iteritems():
            ys.append(name_indices[name])
            xs.append(hour)
            ss.append(count)
    return xs, ys, ss, sorted_names

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--normalize', action='store_true')
    parser.add_argument('git_directory')
    args = parser.parse_args()

    counts = _get_counts(args.git_directory)
    if args.normalize:
        counts = _normalize_counts(counts)
    _gen_plot(*_create_seqs(counts))

if __name__ == '__main__':
    main()
