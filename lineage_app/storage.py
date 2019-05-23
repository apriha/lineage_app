# Copyright 2015 Evernote Corporation
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


# https://github.com/translate/pootle/commit/8ff2463f0b1f1771595334df9ff9f7ba4ec33ae5
@deconstructible
class SendFileFileSystemStorage(FileSystemStorage):
    """Custom storage class, otherwise Django assumes all files are
    uploads headed to `MEDIA_ROOT`.

    Subclassing necessary to avoid messing up with migrations.
    """

    def __init__(self, **kwargs):
        kwargs.update(
            {"location": settings.SENDFILE_ROOT, "file_permissions_mode": 0o640}
        )
        super(SendFileFileSystemStorage, self).__init__(**kwargs)
