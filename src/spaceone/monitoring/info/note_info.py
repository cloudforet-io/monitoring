import functools
from spaceone.api.monitoring.v1 import note_pb2
from spaceone.core import utils
from spaceone.monitoring.model.note_model import Note

__all__ = ['NoteInfo', 'NotesInfo']


def NoteInfo(note_vo: Note, minimal=False):
    info = {
        'note_id': note_vo.note_id,
        'note': note_vo.note,
        'alert_id': note_vo.alert_id,
        'created_by': note_vo.created_by,
    }

    if not minimal:
        info.update({
            'project_id': note_vo.project_id,
            'domain_id': note_vo.domain_id,
            'created_at': utils.datetime_to_iso8601(note_vo.created_at)
        })

    return note_pb2.NoteInfo(**info)


def NotesInfo(note_vos, total_count, **kwargs):
    return note_pb2.NotesInfo(results=list(
        map(functools.partial(NoteInfo, **kwargs), note_vos)), total_count=total_count)
