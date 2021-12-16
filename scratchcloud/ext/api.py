from __future__ import annotations
from typing import List

from ..client import CloudClient
from ..errors import NotFoundError

from datetime import datetime
import asyncio
import aiohttp
from enum import Enum

class NotFound(): pass

def get_keys(d: dict, keys: list, if_not_found = NotFound()):
    for key in keys:
        try: 
            d = d[key]
        except:
            return if_not_found
    return d

class APIClient (CloudClient):
    """A wrapper for CloudClient that interfaces with the scratch API.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def fetch_user(self, username: str) -> 'User':
        """A coroutine that fetches a user from the API.
        
        :param username: The user's name that will be fetched
        :type username: str

        :raises NotFoundError: If the data couldn't be accessed by the scratch API

        :rtype: :class:`ext.api.User`
        """

        PATH = f'https://api.scratch.mit.edu/users/{username}'
        data = await self.http_session.get(PATH)
        data = await data.json()
        if 'code' in data:
            if data['code'] == 'NotFound':
                raise NotFoundError()
        
        return User(self, **data)
    
    async def fetch_project(self, owner_username: str, project_id: str) -> 'Project':
        """A coroutine that fetches a project from the API.
        
        :param owner_username: The username of the owner of the project
        :type owner_username: str
        :param project_id: The id of the project
        :type project_id: str

        :raises NotFoundError: If the data couldn't be accessed by the scratch API

        :rtype: :class:`ext.api.Project`
        """

        PATH = f'https://api.scratch.mit.edu/users/{owner_username}/projects/{project_id}'
        data = await self.http_session.get(PATH)
        data = await data.json()
        if 'code' in data:
            if data['code'] == 'NotFound':
                raise NotFoundError()
        
        return Project(self, **data)
        
    async def fetch_studio(self, studio_id: str) -> 'Studio':
        """A coroutine that fetches a studio from the API.
        
        :param studio_id: The studio id
        :type studio_id: str

        :raises NotFoundError: If the data couldn't be accessed by the scratch API

        :rtype: :class:`ext.api.Studio`
        """

        PATH = f'https://api.scratch.mit.edu/{studio_id}'
        data = await self.http_session.get(PATH)
        data = await data.json()
        if 'code' in data:
            if data['code'] == 'NotFound':
                raise NotFoundError()
        
        return Studio(self, **data)

    async def fetch_message_count(self, username: str) -> int:
        """Fetches message count of a specific user from the api.
        
        :param username: The username of the user to search
        :type username: str

        :raises NotFoundError: If the data couldn't be accessed by the scratch API

        :rtype: int
        """

        PATH = f'https://api.scratch.mit.edu/users/{username}/messages/count'
        data = await self.http_session.get(PATH)
        data = await data.json()
        if 'code' in data:
            if data['code'] == 'NotFound':
                raise NotFoundError()

        return data['count']

class BaseScratchObject():
    """A base for scratch objects.
    If data is not found, it is replaced with the NotFound class.
    """

    def __setattr__(self, name: str, value) -> None:
        if not (isinstance(value, NotFound) and name in self.__dict__.keys()):
            self.__dict__[name] = value  

class User(BaseScratchObject):
    """A scratch User object.
    
    :param client: The client that the user belongs to
    :type client: :class:`ext.api.APIClient`
    :param kwargs: The data received from the API
    :type kwargs: dict
    """

    def __init__(self, client: APIClient, **kwargs):
        self.client = client
        self._update_all(kwargs)

    def _update_all(self, data):
        self.id = get_keys(data, ['id'])
        self.name = get_keys(data, ['username'])
        self.scratchteam = get_keys(data, ['scratchteam'])
        self.joined_at = get_keys(data, ['history', 'joined'])
        if type(self.joined_at) == 'str':
            self.joined_at = datetime.strptime(self.joined_at, "%Y-%m-%dT%H:%M:%S.%f%z")
        
        self.image_90x90 = get_keys(data, ['profile', 'images', '90x90'])
        self.image_60x60 = get_keys(data, ['profile', 'images', '60x60'])
        self.image_55x55 = get_keys(data, ['profile', 'images', '55x55'])
        self.image_50x50 = get_keys(data, ['profile', 'images', '50x50'])
        self.image_32x32 = get_keys(data, ['profile', 'images', '32x32'])

        self.status = get_keys(data, ['profile', 'status'])
        self.bio = get_keys(data, ['profile', 'bio'])
        self.country = get_keys(data, ['profile', 'country'])

    async def fetch_api(self):
        """Fetches data from the API and updates self attributes.
        """

        PATH = f'https://api.scratch.mit.edu/users/{self.name}'
        data = await self.client.http_session.get(PATH)
        data = await data.json()
        self._update_all(data)
    
    async def fetch_favorites(self, limit: int = 20, offset: int = 0) -> List[Project]:
        """Fetches the user's favorite projects from the api.
        
        :param limit: The maximum number of return values,
            default 20
        :type limit: int, optional
        :param offset: The offset for return values,
            default 0
        :type offset: int, optional

        :rtype: List[:class:`ext.api.Project`]
        """

        PATH = f'https://api.scratch.mit.edu/users/{self.name}/favorites?limit={limit}&offset={offset}'
        data = await self.client.http_session.get(PATH)
        data = await data.json()

        projects = []
        for project in data:
            projects.append(Project(client=self.client, **project))
        
        return projects

    async def fetch_followers(self, limit: int = 20, offset: int = 0) -> List[User]:
        """Fetches the user's followers from the api.
        
        :param limit: The maximum number of return values,
            default 20
        :type limit: int, optional
        :param offset: The offset for return values,
            default 0
        :type offset: int, optional

        :rtype: List[:class:`ext.api.User`]
        """

        PATH = f'https://api.scratch.mit.edu/users/{self.name}/followers?limit={limit}&offset={offset}'
        data = await self.client.http_session.get(PATH)
        data = await data.json()

        users = []
        for user in data:
            users.append(User(client=self.client, **user))
        
        return users

    async def fetch_following(self, limit: int = 20, offset: int = 0) -> List[User]:
        """Fetches who the user is following from the api.
        
        :param limit: The maximum number of return values,
            default 20
        :type limit: int, optional
        :param offset: The offset for return values,
            default 0
        :type offset: int, optional

        :rtype: List[:class:`ext.api.User`]
        """

        PATH = f'https://api.scratch.mit.edu/users/{self.name}/following?limit={limit}&offset={offset}'
        data = await self.client.http_session.get(PATH)
        data = await data.json()

        users = []
        for user in data:
            users.append(User(client=self.client, **user))
        
        return users

    async def fetch_projects(self, limit: int = 20, offset: int = 0) -> List[Project]:
        """Fetches the user's projects from the api.
        
        :param limit: The maximum number of return values,
            default 20
        :type limit: int, optional
        :param offset: The offset for return values,
            default 0
        :type offset: int, optional

        :rtype: List[:class:`ext.api.Project`]
        """

        PATH = f'https://api.scratch.mit.edu/users/{self.name}/projects?limit={limit}&offset={offset}'
        data = await self.client.http_session.get(PATH)
        data = await data.json()

        projects = []
        for project in data:
            projects.append(Project(client=self.client, **project))
        
        return projects

class Author(User):
    """A scratch Author object. Identical to User but may have less data at inception.
    
    :param client: The client that the user belongs to
    :type client: :class:`ext.api.APIClient`
    :param kwargs: The data received from the API
    :type kwargs: dict
    """

    pass

class StudioUser(User):
    """A scratch StudioUser object. Identical to User but may have less data at inception.
    
    :param client: The client that the user belongs to
    :type client: :class:`ext.api.APIClient`
    :param kwargs: The data received from the API
    :type kwargs: dict
    """

    pass

class CommentType(Enum):
    """Enum for comments.
    """

    Project = 0
    Studio = 1
    Profile = 2

class Comment(BaseScratchObject):
    """A scratch Comment object.
    
    :param client: The client that the user belongs to
    :type client: :class:`ext.api.APIClient`
    :param kwargs: The data received from the API
    :type kwargs: dict
    """

    def __init__(self, client: APIClient, comment_type: CommentType, **kwargs):
        self.client = client
        self.comment_type = comment_type

        self._update_all(kwargs)
    
    def _update_all(self, data):
        if self.comment_type.value == 0: # Project type
            self.project: Project = get_keys(data, ['project'])
        if self.comment_type.value == 1: # Studio type
            self.studio: Studio = get_keys(data, ['studio'])

        self.id = get_keys(data, ['id'])
        self.parent_id = get_keys(data, ['parent_id'])
        self.parent_author_id = get_keys(data, ['commentee_id'])
        self.content = get_keys(data, ['content'])

        self.created_at = get_keys(data, ['datetime_created'])
        if type(self.created_at) == 'str':
            self.created_at = datetime.strptime(self.created_at, "%Y-%m-%dT%H:%M:%S.%f%z")

        self.modified_at = get_keys(data, ['datetime_modified'])
        if type(self.modified_at) == 'str':
            self.modified_at = datetime.strptime(self.modified_at, "%Y-%m-%dT%H:%M:%S.%f%z")

        self.visibility = get_keys(data, ['visibility'])
        self.reply_count = get_keys(data, ['reply_count']) 

        self.author = Author(self.client, **get_keys(data, ['author']))
    
    async def fetch_replies(self, limit: int = 20, offset: int = 0) -> List[Reply]:
        """Fetches the comment's replies from the api.
        
        :param limit: The maximum number of return values,
            default 20
        :type limit: int, optional
        :param offset: The offset for return values,
            default 0
        :type offset: int, optional

        :rtype: List[:class:`ext.api.Reply`]
        """

        if self.comment_type.value == 0: # Project type
            PATH = f'https://api.scratch.mit.edu/users/{self.project.author.name}/projects/{self.project.id}/comments/{self.id}/replies?offset={offset}&limit={limit}'
        elif self.comment_type.value == 1: # Studio type
            PATH = f'https://api.scratch.mit.edu/studios/{self.studio.id}/comments/{self.id}/replies?offset={offset}&limit={limit}'
        
        data = await self.client.http_session.get(PATH)
        data = await data.json()

        comments = []
        for comment in data:
            if self.comment_type.value == 0: # Project type
                comments.append(Reply(self.client, self.comment_type, project = self.project, **comment))
            elif self.comment_type.value == 1: # Studio type
                comments.append(Reply(self.client, self.comment_type, studio = self.studio, **comment))

        return comments

class Reply(Comment):
    """A scratch Reply object.
    
    :param client: The client that the user belongs to
    :type client: :class:`ext.api.APIClient`
    :param kwargs: The data received from the API
    :type kwargs: dict
    """
    
    pass

class Project(BaseScratchObject):
    """A scratch Project object.
    
    :param client: The client that the user belongs to
    :type client: :class:`ext.api.APIClient`
    :param kwargs: The data received from the API
    :type kwargs: dict
    """
   
    def __init__(self, client: APIClient, **kwargs):
        self.client = client
        self.project_json = None
        
        self._update_all(kwargs)

    def _update_all(self, data):
        self.id = get_keys(data, ['id'])
        self.title = get_keys(data, ['title'])
        self.description = get_keys(data, ['description'])
        self.instructions = get_keys(data, ['instructions'])
        self.visibility = get_keys(data, ['visibility'])
        self.public = get_keys(data, ['public'])
        self.comments_allowed = get_keys(data, ['comments_allowed'])
        self.is_published = get_keys(data, ['is_published'])

        self.author = Author(self.client, **get_keys(data, ['author']))

        self.image = get_keys(data, ['image'])
        self.created_at = get_keys(data, ['history', 'created'])
        if type(self.created_at) == 'str':
            self.created_at = datetime.strptime(self.created_at, "%Y-%m-%dT%H:%M:%S.%f%z")

        self.modified_at = get_keys(data, ['history', 'modified'])
        if type(self.modified_at) == 'str':
            self.modified_at = datetime.strptime(self.modified_at, "%Y-%m-%dT%H:%M:%S.%f%z")

        self.shared_at = get_keys(data, ['history', 'shared'])
        if type(self.shared_at) == 'str':
            self.shared_at = datetime.strptime(self.shared_at, "%Y-%m-%dT%H:%M:%S.%f%z")
         


        self.views = get_keys(data, ['stats', 'views'])
        self.loves = get_keys(data, ['stats', 'loves'])
        self.favorites = get_keys(data, ['stats', 'favorites'])
        self.remixes = get_keys(data, ['stats', 'remixes'])

        self.remix_parent = get_keys(data, ['remix', 'parent'])
        self.remix_root = get_keys(data, ['remix', 'root'])

    async def fetch_api(self):
        """Fetches data from the API and updates self attributes.
        """

        PATH = f'https://api.scratch.mit.edu/projects/{self.id}'
        data = await self.client.http_session.get(PATH)
        data = await data.json()
        self._update_all(data)
    
    async def fetch_comments(self, limit: int = 20, offset: int = 0) -> List[Comment]:
        """Fetches the project's comments from the api.
        
        :param limit: The maximum number of return values,
            default 20
        :type limit: int, optional
        :param offset: The offset for return values,
            default 0
        :type offset: int, optional

        :rtype: List[:class:`ext.api.Comment`]
        """

        PATH = f'https://api.scratch.mit.edu/users/{self.author.name}/projects/{self.id}/comments?offset={offset}&limit={limit}'
        data = await self.client.http_session.get(PATH)
        data = await data.json()
        
        comments = []
        for comment in data:
            comments.append(Comment(self.client, CommentType(0), project = self, **comment))
        
        return comments
    
    async def fetch_project_json(self) -> dict:
        """Fetches the project's json from the api.

        :rtype: dict
        """

        PATH = f'https://projects.scratch.mit.edu/{self.id}'
        data = await self.client.http_session.get(PATH)
        data = await data.json()

        self.project_json = data
        return data

    async def fetch_block_count(self) -> int:
        """Fetches the project's block count from the project api.
        
        :rtype: int
        """

        project = await self.fetch_project_json()

        blocks = 0
        for sprite in project['targets']:
            blocks += len(sprite['blocks'])
    
        return blocks
    
    async def fetch_sprite_count(self) -> int:
        """Fetches the project's sprite count from the project api.

        :rtype: int
        """

        project = await self.fetch_project_json()

        return len(project['targets'])

class StudioProject(Project):
    """A scratch StudioProject object. Identical to User but may have less data at inception.
    
    :param client: The client that the user belongs to
    :type client: :class:`ext.api.APIClient`
    :param kwargs: The data received from the API
    :type kwargs: dict
    """
   
    pass

class Studio(BaseScratchObject):
    """A scratch Studio object.
    
    :param client: The client that the user belongs to
    :type client: :class:`ext.api.APIClient`
    :param kwargs: The data received from the API
    :type kwargs: dict
    """

    def __init__(self, client: APIClient, **kwargs):
        self.client = client
        self._update_all(kwargs)
    
    def _update_all(self, data):
        self.id = get_keys(data, ['id'])
        self.title = get_keys(data, ['title'])
        self.host_id = get_keys(data, ['host'])
        self.description = get_keys(data, ['description'])
        self.visibility = get_keys(data, ['visibility'])
        self.public = get_keys(data, ['public'])
        self.open_to_all = get_keys(data, ['open_to_all'])
        self.comments_allowed = get_keys(data, ['comments_allowed'])
        self.image = get_keys(data, ['image'])

        self.created_at = get_keys(data, ['created'])
        if type(self.created_at) == 'str':
            self.created_at = datetime.strptime(self.created_at, "%Y-%m-%dT%H:%M:%S.%f%z")

        self.modified_at = get_keys(data, ['modified'])
        if type(self.modified_at) == 'str':
            self.modified_at = datetime.strptime(self.modified_at, "%Y-%m-%dT%H:%M:%S.%f%z")

        self.num_comments = get_keys(data, ['comments'])
        self.num_followers = get_keys(data, ['followers'])
        self.num_managers = get_keys(data, ['managers'])
        self.num_projects = get_keys(data, ['projects'])

    async def fetch_api(self):
        """Fetches data from the API and updates self attributes.
        """

        PATH = f'https://api.scratch.mit.edu/studios/{self.id}'
        data = await self.client.http_session.get(PATH)
        data = await data.json
        self._update_all(data)

    async def fetch_projects(self, limit: int = 24, offset: int = 0) -> List[StudioProject]:
        """Fetches the studio's projects from the api.
        
        :param limit: The maximum number of return values,
            default 24
        :type limit: int, optional
        :param offset: The offset for return values,
            default 0
        :type offset: int, optional

        :rtype: List[:class:`ext.api.StudioProject`]
        """

        PATH = f'https://api.scratch.mit.edu/studios/{self.id}/projects/?limit={limit}&offset={offset}'
        data = await self.client.http_session.get(PATH)
        data = await data.json()
        projects = []
        for proj in data:
            projects.append(
                StudioProject(
                    client = self.client,

                    id = proj['id'], 
                    title = proj['title'], 
                    image = proj['image'], 
                    author = {
                        'id': proj['creator_id'],
                        'username': proj['username']
                    }))
        
        return projects

    async def fetch_comments(self, limit: int = 20, offset: int = 0) -> List[Comment]:
        """Fetches the studio's comments from the api.
        
        :param limit: The maximum number of return values,
            default 20
        :type limit: int, optional
        :param offset: The offset for return values,
            default 0
        :type offset: int, optional

        :rtype: List[:class:`ext.api.Comment`]
        """

        PATH = f'https://api.scratch.mit.edu/studios/{self.id}/comments?limit={limit}&offset={offset}'
        data = await self.client.http_session.get(PATH)
        data = await data.json()

        comments = []
        for comment in data:
            comments.append(Comment(self.client, CommentType(1), studio = self, **comment))
        
        return comments

    async def fetch_managers(self, limit: int = 40, offset: int = 0) -> List[StudioUser]:
        """Fetches the studio's managers from the api.
        
        :param limit: The maximum number of return values,
            default 40
        :type limit: int, optional
        :param offset: The offset for return values,
            default 0
        :type offset: int, optional

        :rtype: List[:class:`ext.api.StudioUser`]
        """

        PATH = f'https://api.scratch.mit.edu/studios/{self.id}/managers/?limit={limit}&offset={offset}'
        data = await self.client.http_session.get(PATH)
        data = await data.json()

        users = []
        for user in data:
            users.append(StudioUser(self.client, **user))
        
        return users
    
    async def fetch_curators(self, limit: int = 40, offset: int = 0) -> List[StudioUser]:
        """Fetches the studio's curators from the api.
        
        :param limit: The maximum number of return values,
            default 40
        :type limit: int, optional
        :param offset: The offset for return values,
            default 0
        :type offset: int, optional

        :rtype: List[:class:`ext.api.StudioUser`]
        """

        PATH = f'https://api.scratch.mit.edu/studios/{self.id}/curators/?limit={limit}&offset={offset}'
        data = await self.client.http_session.get(PATH)
        data = await data.json()

        users = []
        for user in data:
            users.append(StudioUser(self.client, **user))
        
        return users

# TODO
# Add Regex or bs4 for site-api (followers#, following#, etc)
# Add project.fetch_cloud() and ValidateCloud: https://clouddata.scratch.mit.edu/logs?projectid=id&limit=100&offset=0
