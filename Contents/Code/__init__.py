# -*- coding: utf-8 -*-

from contextlib import closing
import mysql.connector
import datetime
import pickle
import urllib

date_fmt = "%d.%m.%y %H:%M"
cnx = None


def date(tm):
    return tm.strftime( date_fmt )

def enc(s):
    return s.encode("UTF-8")


def dec(s):
    return s.decode("UTF-8")


def conn():
    cnx = mysql.connector.connect(user=Prefs["user"], password=Prefs["password"],
                              host=Prefs["server"], port=int(Prefs["port"]),
                              database=Prefs["database"])
    return closing(cnx)


@handler("/video/argustv", "Title")
def Main():
    oc = ObjectContainer(
        objects=[
            DirectoryObject(key=Callback(GroupBy, group_by="ScheduleName", order_by="max(ProgramStartTime) DESC"), title="Schedules / latest recordings first"),
            DirectoryObject(key=Callback(GroupBy, group_by="ScheduleName", order_by="ScheduleName"), title="Schedules / alphabetically"),
            DirectoryObject(key=Callback(GroupBy, group_by="Title", order_by="max(ProgramStartTime) DESC"), title="Titles / latest recordings first"),
            DirectoryObject(key=Callback(GroupBy, group_by="Title", order_by="Title"), title="Titles / alphabetically"),
            DirectoryObject(key=Callback(Latest, number=10), title="Latest 10 recordings"),
            ])
    return oc

@route('/video/argustv/groupby')
def GroupBy(group_by, order_by):
    objects = []
    with conn() as cnx:
        with closing(cnx.cursor()) as cursor:
            sql = "SELECT %s, max(ProgramStartTime), count(RecordingId) FROM Recording WHERE ChannelType = 0 AND PendingDelete = 0 GROUP BY %s ORDER BY %s" %\
                  (group_by, group_by, order_by)
            cursor.execute(sql)
            for row in cursor:
                title = "%s (%d) - %s" % (row[0], row[2], row[1])
                objects.append(TVShowObject(key=Callback(Recordings, key=group_by, value=enc(row[0])), title=title, episode_count=row[2], rating_key=row[0]))
        oc = ObjectContainer(objects=objects)
        return oc


@route('/video/argustv/latest')
def Latest(number):
    oc = ObjectContainer(title2="Latest %d" % (int(number)))
    with conn() as cnx:
        with closing(cnx.cursor()) as cursor:
            sql = "SELECT RecordingId, Title, SubTitle, EpisodeNumberDisplay, ProgramStartTime, Description, RecordingFileName FROM Recording WHERE ChannelType = 0 AND PendingDelete = 0 ORDER BY ProgramStartTime DESC LIMIT %s"
            cursor.execute(sql, (int(number), ))
            for row in cursor:
                try:
                    oc.add(CreateRecordingFromSQL(row, include_title=True))
                except Exception as e:
                    Log.Debug(e)
        return oc


def CreateRecordingFromSQL(row, include_title, container=False):
    recording_id, title, sub_title, episode, start, plot, file = row

    start = date(start)

    #tn= getThumbnailURL( d[ "RecordingId" ], 512 )

    if not sub_title:
        show = ""
    else:
        show = title
        title = sub_title

    if not include_title:
        show = ""

    if container:
        if show:
            title = show + " / " + title
            show = ""
        title = str(start) + ": " + title
    else:
        show = str(start) + ": " + show

    if episode:
        summary = episode + ": " + plot
    else:
        summary = plot

    eo = EpisodeObject(title=title, summary=summary, show=show, key=Callback(CreateRecording, recording_id=recording_id, container=True),
                    rating_key=recording_id,
                    items=[MediaObject(parts=[PartObject(key=recording_id, file=urllib.quote(file.encode("UTF-8"), safe="/\ "))])])

    if container:
        return ObjectContainer(objects=[eo])
    else:
        return eo

@route('/video/argustv/createrecording')
def CreateRecording(recording_id, container=False):
    with conn() as cnx:
        with closing(cnx.cursor()) as cursor:
            sql = "SELECT RecordingId, Title, SubTitle, EpisodeNumberDisplay, ProgramStartTime, Description, RecordingFileName FROM Recording WHERE RecordingId = %s"
            cursor.execute(sql, (recording_id, ))
            for row in cursor:
                return CreateRecordingFromSQL(row, include_title=True, container=container)


@route('/video/argustv/recordings')
def Recordings(key, value):
    value = dec(value)
    oc = ObjectContainer(title2=value)
    with conn() as cnx:
        with closing(cnx.cursor()) as cursor:
            sql = "SELECT RecordingId, Title, SubTitle, EpisodeNumberDisplay, ProgramStartTime, Description, RecordingFileName FROM Recording WHERE %s = %s AND ChannelType = 0 AND PendingDelete = 0 ORDER BY ProgramStartTime DESC" %\
                (key, "%s")
            cursor.execute(sql, (value, ))
            for row in cursor:
                try:
                    oc.add(CreateRecordingFromSQL(row, include_title=False))
                except Exception as e:
                    Log.Debug(e)

        return oc

