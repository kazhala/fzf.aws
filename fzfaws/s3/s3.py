"""Contains the s3 wrapper class."""
import os
import re
import itertools
from typing import Any, Dict, Generator, List, Optional, Sequence, Tuple, Union

from botocore.exceptions import ClientError

from fzfaws.utils import BaseSession, FileLoader, Pyfzf, Spinner, get_confirmation
from fzfaws.utils.exceptions import (
    InvalidFileType,
    InvalidS3PathPattern,
    NoSelectionMade,
)


class S3(BaseSession):
    """Wrapper class for s3 to interact with s3.

    Handles the bucket operation and object operation.

    :param profile: profile to use for this operation
    :type profile: Union[bool, str], optional
    :param region: region to use for this operation
    :type region: Union[bool, str], optional
    """

    def __init__(
        self,
        profile: Optional[Union[str, bool]] = None,
        region: Optional[Union[str, bool]] = None,
    ) -> None:
        """Construct the s3 instance."""
        super().__init__(profile=profile, region=region, service_name="s3")
        self.bucket_name: str = ""
        self.path_list: List[str] = [""]

    def set_s3_bucket(self, header: str = "") -> None:
        """List bucket through fzf and let user select a bucket.

        :param header: header to display in fzf header
        :type header: str, optional
        """
        fzf = Pyfzf()
        with Spinner.spin(message="Fethcing s3 buckets ..."):
            response = self.client.list_buckets()
        fzf.process_list(response["Buckets"], "Name")
        self.bucket_name = str(fzf.execute_fzf(header=header))

    def set_bucket_and_path(self, bucket: str = None) -> None:
        """Set both bucket and path.

        This is used to process argument of "-b bucket/object", if any of them is set,
        skip further fzf selection. 
        
        E.g. if bucket is set, skip select bucket. If both bucket and object is set, skip
        all fzf selection.

        :param bucket: bucket/path to set, format(Bucket/ or Bucket/path/ or Bucket/filename)
        :type bucket: str, optional
        :raises InvalidS3PathPattern: whne the input format is not valid
        """
        if not bucket:
            return

        # check user input
        result, match = self._validate_input_path(bucket)
        if result == "accesspoint":
            self.bucket_name = match[0][:-1]
            self.path_list[0] = match[1]
        elif result == "bucketpath":
            self.bucket_name = match[0][:-1]
            self.path_list[0] = match[1]
        else:
            raise InvalidS3PathPattern(
                "Invalid s3 path pattern, valid pattern(Bucket/ or Bucket/path/ or Bucket/filename)"
            )

    def set_s3_path(self, download: bool = False) -> None:
        """Set 'path' of s3 to upload or download.

        s3 folders are not actually folder, found this path listing on
        https://github.com/boto/boto3/issues/134#issuecomment-116766812

        This method would set the 'path' for s3 however the self.path_list cannot be used
        as the destination of upload immediately. This only set the path
        without handling different upload sceanario. Please use the
        get_s3_destination_key after set_s3_path to obtain the correct destination key

        :param download: if not download, add append option
        :type download: bool, optional
        :raises NoSelectionMade: when user did not make a bucket selection, exit
        """
        selected_option = self._get_path_option(download=download)

        if selected_option == "input":
            self.path_list[0] = input("Input the path(newname or newpath/): ")
        elif selected_option == "root":
            print("S3 file path is set to root")
        elif selected_option == "append" or selected_option == "interactively":
            paginator = self.client.get_paginator("list_objects")
            fzf = Pyfzf()
            try:
                parents = []
                # interactively search down 'folders' in s3
                while True:
                    if len(parents) > 0:
                        fzf.append_fzf("..\n")
                    with Spinner.spin(message="Fetching s3 objects ..."):
                        preview: str = ""
                        for result in paginator.paginate(
                            Bucket=self.bucket_name,
                            Prefix=self.path_list[0],
                            Delimiter="/",
                        ):
                            for prefix in result.get("CommonPrefixes", []):
                                fzf.append_fzf("%s\n" % prefix.get("Prefix"))
                            for content in result.get("Contents", []):
                                preview += content.get("Key")
                                preview += "^"

                    # has to use tr to transform the string to new line during preview by fzf
                    # not sure why, but if directly use \n, fzf preview interpret as a new command
                    # TODO: findout why
                    selected_path = str(
                        fzf.execute_fzf(
                            empty_allow=True,
                            print_col=0,
                            header="PWD: s3://%s/%s (press ESC to use current path)"
                            % (self.bucket_name, self.path_list[0]),
                            preview="echo %s | tr '^' '\n'" % preview.rstrip(),
                        )
                    )
                    if not selected_path:
                        raise NoSelectionMade
                    if selected_path == "..":
                        self.path_list[0] = parents.pop()
                    else:
                        parents.append(self.path_list[0])
                        self.path_list[0] = selected_path
                    # reset fzf string
                    fzf.fzf_string = ""
            except ClientError:
                raise
            except KeyboardInterrupt:
                raise
            except:
                if selected_option == "append":
                    print(
                        "Current PWD is s3://%s/%s"
                        % (self.bucket_name, self.path_list[0])
                    )
                    new_path = input(
                        "Input the new path to append(newname or newpath/): "
                    )
                    self.path_list[0] += new_path
                if get_confirmation(
                    "S3 file path will be set to s3://%s/%s"
                    % (self.bucket_name, self.path_list[0],)
                ):
                    print(
                        "S3 file path is set to %s"
                        % (self.path_list[0] if self.path_list[0] else "root")
                    )
                else:
                    raise NoSelectionMade("S3 file path was not configured, exiting..")

    def set_s3_object(
        self,
        version: bool = False,
        multi_select: bool = False,
        deletemark: bool = False,
    ) -> None:
        """List object within a bucket and let user select a object.

        Stores the file path and the filetype into the instance attributes
        using paginator to get all results.

        All of the deleted object are displayed in red color when version mode
        is enabled.

        :param version: enable version search
        :type version: bool, optional
        :param multi_select: enable multi selection
        :type multi_select: bool, optional
        :param deletemark: show deletemark object in the list
        :type deletemark: bool, optional
        :raises NoSelectionMade: when there is no selection made
        """
        fzf = Pyfzf()

        if not version:
            paginator = self.client.get_paginator("list_objects")
            with Spinner.spin(message="Fetching s3 objects ..."):
                for result in paginator.paginate(Bucket=self.bucket_name):
                    for file in result.get("Contents", []):
                        if file.get("Key").endswith("/") or not file.get("Key"):
                            # user created dir in S3 console will appear in the result and is not operatable
                            continue
                        fzf.append_fzf("Key: %s\n" % file.get("Key"))
            if multi_select:
                self.path_list = list(fzf.execute_fzf(print_col=-1, multi_select=True))
            else:
                self.path_list[0] = str(fzf.execute_fzf(print_col=-1))

        else:
            paginator = self.client.get_paginator("list_object_versions")
            with Spinner.spin(message="Fetching s3 objects ..."):
                results = paginator.paginate(Bucket=self.bucket_name)
                version_obj_genrator = self._uniq_object_generator(results, deletemark)
                generated = False
                for item in version_obj_genrator:
                    generated = True
                    fzf.append_fzf(item + "\n")
                if not generated:
                    raise NoSelectionMade
            if multi_select:
                self.path_list = list(fzf.execute_fzf(print_col=-1, multi_select=True))
            else:
                self.path_list[0] = str(fzf.execute_fzf(print_col=-1))

    def get_object_version(
        self,
        bucket: str = "",
        key: str = "",
        delete: bool = False,
        select_all: bool = False,
        non_current: bool = False,
        multi_select: bool = True,
    ) -> List[Dict[str, str]]:
        """List object versions through fzf.
        
        :param bucket: object's bucketname, if not set, class instance's bucket_name will be used
        :type bucket: str, optional
        :param key: object's key, if not set, class instance's path_list[0] will be used
        :type key: str, optional
        :param delete: allow to choose delete marker
        :type delete: bool, optional
        :param select_all: skip fzf and select all version and put into return list
        :type select_all: bool, optional
        :param non_current: only put non_current versions into list
        :type non_current: bool, optional
        :param multi_select: allow multi selection
        :type multi_select: bool, optional
        :return: list of selected versions
        :rtype: List[Dict[str, str]]

        Example return value:
            [{'Key': s3keypath, 'VersionId': s3objectid}]
        """
        bucket = bucket if bucket else self.bucket_name
        key_list: list = []

        if key:
            key_list.append(key)
        else:
            key_list.extend(self.path_list)
        selected_versions: list = []
        for key in key_list:
            response_generator: Union[list, Generator[Dict[str, str], None, None]] = []
            paginator = self.client.get_paginator("list_object_versions")
            for result in paginator.paginate(Bucket=bucket, Prefix=key):
                response_generator = self._version_generator(
                    result.get("Versions", []),
                    result.get("DeleteMarkers", []),
                    non_current,
                    delete,
                )
            if not select_all:
                fzf = Pyfzf()
                fzf.process_list(
                    response_generator,
                    "VersionId",
                    "Key",
                    "IsLatest",
                    "DeleteMarker",
                    "LastModified",
                )
                if delete and multi_select:
                    for result in fzf.execute_fzf(multi_select=True):
                        selected_versions.append({"Key": key, "VersionId": result})
                else:
                    selected_versions.append(
                        {"Key": key, "VersionId": str(fzf.execute_fzf())}
                    )
            else:
                selected_versions.extend(
                    [
                        {"Key": key, "VersionId": version.get("VersionId")}
                        for version in response_generator
                    ]
                )
        return selected_versions

    def get_object_data(self, file_type: str = "") -> Dict[str, Any]:
        """Read the s3 object.

        Read the s3 object file and if is yaml/json file_type, load the file into dict
        currently is only used for cloudformation.

        :param file_type: type of file to process, supported value: yaml/json
        :type file_type: str
        :return: processed dict of json or yaml
        :raises InvalidFileType: when the file_type is invalid
        :rtype: Dict[str, Any]
        """
        with Spinner.spin(message="Reading file from s3 ..."):
            s3_object = self.resource.Object(self.bucket_name, self.path_list[0])
            body = s3_object.get()["Body"].read()
            body_dict: Dict[str, Any] = {}
            fileloader = FileLoader(body=body)
            if file_type == "yaml":
                body_dict = fileloader.process_yaml_body()
            elif file_type == "json":
                body_dict = fileloader.process_json_body()
            else:
                raise InvalidFileType
        return body_dict

    def get_object_url(self, version: str = "", object_key: str = "") -> str:
        """Return the object url of the current selected object.

        :param version: get url for versioned object
        :type version: str, optional
        :param object_key: s3 object_key
        :type object_key: str, optional
        :return: s3 url for the object
        :rtype: str
        """
        if not object_key:
            object_key = self.path_list[0]

        response = self.client.get_bucket_location(Bucket=self.bucket_name)
        bucket_location = response["LocationConstraint"]
        if not version:
            return "https://s3-%s.amazonaws.com/%s/%s" % (
                bucket_location,
                self.bucket_name,
                object_key,
            )
        else:
            return "https://s3-%s.amazonaws.com/%s/%s?versionId=%s" % (
                bucket_location,
                self.bucket_name,
                object_key,
                version,
            )

    def get_s3_destination_key(self, local_path: str, recursive: bool = False) -> str:
        """Set the s3 key for upload destination.

        Check if the current s3 path ends with '/'.
        If not, pass, since is already a valid path.
        If yes, append the local file name to the s3 path as the key.

        If recursive is set, append '/' to last if '/' does not exist.

        :param local_path: local path for download
        :type local_path: str
        :param recursive: indicates if it is recursive operation
        :type recursive: bool, optional
        :return: formated destination key can be used by boto3
        :rtype: str
        """
        if recursive:
            if not self.path_list[0]:
                return local_path
            else:
                return os.path.join(self.path_list[0], local_path)

        else:
            if not self.path_list[0]:
                # if operation is at root level, return the file name
                return os.path.basename(local_path)
            elif self.path_list[0].endswith("/"):
                # if specified s3 path, append the file name
                return os.path.join(self.path_list[0], os.path.basename(local_path))
            else:
                return self.path_list[0]

    def _validate_input_path(
        self, user_input
    ) -> Union[
        Tuple[str, Sequence[str]], Tuple[str, Sequence[str]], Tuple[None, None],
    ]:
        """Validate if the user input path is valid format.

        :param user_input: the input from -b flag
        :type user_input: str
        :return: tuple of bucket type and bucket path
        :rtype: Union[
            Tuple[Literal["accesspoint"], Sequence[str]],
            Tuple[Literal["bucketpath"], Sequence[str]],
            Tuple[None, None],
        ]
        """
        accesspoint_pattern = r"^(arn:aws.*:s3:[a-z\-0-9]+:[0-9]{12}:accesspoint[/:][a-zA-Z0-9\-]{1,63}/)(.*)$"
        path_pattern = r"^(?!arn:.*)(.*?/)(.*)$"
        if re.match(accesspoint_pattern, user_input):
            return ("accesspoint", re.match(accesspoint_pattern, user_input).groups())
        elif re.match(path_pattern, user_input):
            return ("bucketpath", re.match(path_pattern, user_input).groups())
        else:
            return (None, None)

    def _get_path_option(self, download: bool = False) -> str:
        """Pop fzf for user to select what to do with the path.

        :param download: if not download, insert append option
        :type download: bool, optional
        :return: selected option
        :rtype: str
        """
        fzf = Pyfzf()
        fzf.append_fzf("root: operate on the root level of the bucket\n")
        fzf.append_fzf("interactively: interactively select a path through s3\n")
        fzf.append_fzf("input: manully input the path/name\n")
        if not download:
            fzf.append_fzf(
                "append: interactively select a path and then input new path/name to append"
            )
        selected_option = str(
            fzf.execute_fzf(
                print_col=1,
                header="Please select which level of the bucket would you like to operate in",
            )
        )
        return selected_option.split(":")[0]

    def _version_generator(
        self, versions: List[dict], markers: List[dict], non_current: bool, delete: bool
    ) -> Generator[Dict[str, str], None, None]:
        """Create version generator to reduce memory usage.

        :param versions: list of versions from list_object_versions paginator
        :type versions: List[dict]
        :param markers: list of delete markers from list_object_versions paginator
        :type markers: List[dict]
        :param non_current: just include non_current object?
        :type non_current: bool
        :param delete: include delete marker
        :type delete: bool
        :return: formatted dict of version information in generator form
        :rtype: Generator[Dict[str,str], None, None]
        """
        for version in versions:
            if (non_current and not version.get("IsLatest")) or not non_current:
                yield {
                    "VersionId": version.get("VersionId"),
                    "Key": version.get("Key"),
                    "IsLatest": version.get("IsLatest"),
                    "DeleteMarker": False,
                    "LastModified": version.get("LastModified"),
                }

        if delete:
            for marker in markers:
                yield {
                    "VersionId": marker.get("VersionId"),
                    "Key": marker.get("Key"),
                    "IsLatest": marker.get("IsLatest"),
                    "DeleteMarker": True,
                    "LastModified": marker.get("LastModified"),
                }

    def _uniq_object_generator(
        self, results: List[Dict[str, Any]], onlydelete: bool
    ) -> Generator[str, None, None]:
        """Create uniq version generator.

        Attempt to improve the performance on big data sets. Comparing with previous
        solutions, although this handle one less edge case (if user delete a version object
        but then created a new object with the same name), this is much faster and better
        in memory usage.
        
        :param results: the result from boto3 paginator
        :type results: List[Dict[str, Any]]
        :param onlydelete: boolean indicator indicates whether to only show deletemark.
            This is only used by delete operation with "-d, --deletemark" flag.
        :type onlydelete: bool
        :return: return the uniq object generator
        :rtype: Generator[str, None, None]
        """

        def _uniq(version_obj):
            return version_obj.get("Key")

        for result in results:
            deletemarks = itertools.groupby(result.get("DeleteMarkers", []), _uniq)
            delete_sets = set()
            for deletemark, _ in deletemarks:
                delete_sets.add(deletemark)

            for deletemark in delete_sets:
                if deletemark.endswith("/"):
                    continue
                yield "\033[31m" + "Key: %s" % deletemark + "\033[0m"

            if not onlydelete:
                for version, _ in itertools.groupby(result.get("Versions", []), _uniq):
                    if version.endswith("/") or version in delete_sets:
                        continue
                    else:
                        yield "Key: %s" % version
