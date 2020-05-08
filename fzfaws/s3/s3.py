"""s3 client wrapper 

A centralized position to initial boto3.client('s3'), better
management if user decide to change region or use different profile
"""
import re
from botocore.exceptions import ClientError
from fzfaws.utils.session import BaseSession
from fzfaws.utils.pyfzf import Pyfzf
from fzfaws.cloudformation.helper.process_file import (
    process_yaml_body,
    process_json_body,
)
from fzfaws.utils.exceptions import InvalidS3PathPattern, NoSelectionMade
from fzfaws.utils.util import get_confirmation
from fzfaws.utils.spinner import Spinner


class S3(BaseSession):
    """handles operation for all s3 related task with boto3.client('s3')

    :param profile: profile to use for this operation
    :type profile: Union[bool, str], optional
    :param region: region to use for this operation
    :type region: Union[bool, str], optional
    """

    def __init__(self, profile=None, region=None):
        super().__init__(profile=profile, region=region, service_name="s3")
        self.bucket_name = ""  # type: str
        self.bucket_path = ""
        self.path_list = [""]  # type: list

    def set_s3_bucket(self, header=""):
        """list bucket through fzf and let user select a bucket

        :param header: header to display in fzf header
        :type header: str, optional
        """
        fzf = Pyfzf()
        spinner = Spinner()
        response = spinner.execute_with_spinner(self.client.list_buckets)
        fzf.process_list(response["Buckets"], "Name")
        self.bucket_name = str(fzf.execute_fzf(header=header))

    def set_bucket_and_path(self, bucket=None):
        """method to set both bucket and path, skip fzf selection

        :param bucket: bucket/path to set, format(Bucket/ or Bucket/path/ or Bucket/filename)
        :type bucket: str, optional
        :raises InvalidS3PathPattern: whne the input format is not valid
        """
        if not bucket:
            return
        # check user input
        result, match = self._validate_input_path(bucket)
        if result == "accesspoint":
            self.bucket_name = match[0][0:-1]
            self.path_list[0](match[1])
            # self.bucket_path = match[1]
            # if self.bucket_path:
            #     self.path_list.append(self.bucket_path)
        elif result == "bucketpath":
            self.bucket_name = bucket.split("/")[0]
            self.path_list[0] = "/".join(bucket.split("/")[1:])
            # self.bucket_path = "/".join(bucket.split("/")[1:])
            # if self.bucket_path:
            #     self.path_list.append(self.bucket_path)
        else:
            raise InvalidS3PathPattern(
                "Invalid s3 path pattern, valid pattern(Bucket/ or Bucket/path/ or Bucket/filename)"
            )

    def set_s3_path(self):
        """set 'path' of s3 to upload or download

        s3 folders are not actually folder, found this path listing on
        https://github.com/boto/boto3/issues/134#issuecomment-116766812

        This method would set the 'path' for s3 however the self.path_list cannot be used
        as the destination of upload immediately. This only set the path
        without handling different upload sceanario. Please use the
        get_s3_destination_key after set_s3_path to obtain the correct destination key

        :raises NoSelectionMade: when user did not make a bucket selection, exit
        """
        selected_option = self._get_path_option()
        if selected_option == "input":
            # self.bucket_path = input("Input the path(newname or newpath/): ")
            # bucket_path = input("Input the path(newname or newpath/): ")
            # self.path_list.append(bucket_path)
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
                    spinner = Spinner()
                    spinner.start()
                    if len(parents) > 0:
                        fzf.append_fzf("..\n")
                    preview = ""  # type: str
                    for result in paginator.paginate(
                        Bucket=self.bucket_name, Prefix=self.path_list[0], Delimiter="/"
                    ):
                        for prefix in result.get("CommonPrefixes", []):
                            fzf.append_fzf(prefix.get("Prefix"))
                            fzf.append_fzf("\n")
                        for content in result.get("Contents", []):
                            preview += content.get("Key")
                            preview += " "
                    spinner.stop()

                    # has to use tr to transform the string to new line during preview by fzf
                    # not sure why, but if directly use \n, fzf preview interpret as a new command
                    # TODO: findout why
                    selected_path = fzf.execute_fzf(
                        empty_allow=True,
                        print_col=0,
                        header="PWD: s3://%s/%s (press ESC to use current path)"
                        % (self.bucket_name, self.path_list[0]),
                        preview="echo %s | tr ' ' '\n'" % preview.rstrip(),
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
            finally:
                Spinner.clear_spinner()

    def set_s3_object(self, version=False, multi_select=False, deletemark=False):
        """list object within a bucket and let user select a object.

        stores the file path and the filetype into the instance attributes
        using paginator to get all results

        Args:
            version: bool, enable version find
                when this set to true, the object search would search through 'list_object_versions'
                rather than list_objects so that user could still find the object even after
                they deleted the object
            multi_select: bool, enable multi_select
            deletemark: bool, only display object that has deletemark associated with
                Only works with version=True
        Exceptions:
            NoSelectionMade: when there is no selection made, bucket is empty
            ClientError: boto3 error
        """
        if not version:
            fzf = Pyfzf()
            paginator = self.client.get_paginator("list_objects")
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
            fzf = Pyfzf()
            key_list = []
            paginator = self.client.get_paginator("list_object_versions")
            for result in paginator.paginate(Bucket=self.bucket_name):
                for version in result.get("DeleteMarkers", []):
                    if version.get("Key").endswith("/") or not version.get("Key"):
                        continue
                    color_string = (
                        "\033[31m" + "Key: %s" % version.get("Key") + "\033[0m"
                    )
                    if color_string not in key_list:
                        key_list.append(color_string)
                if not deletemark:
                    for version in result.get("Versions", []):
                        if version.get("Key").endswith("/") or not version.get("Key"):
                            continue
                        color_string = (
                            "\033[31m" + "Key: %s" % version.get("Key") + "\033[0m"
                        )
                        norm_string = "Key: %s" % version.get("Key")
                        if color_string not in key_list and norm_string not in key_list:
                            key_list.append(norm_string)
                        elif color_string in key_list and version.get("IsLatest"):
                            # handle the case where delete marker is associated, object is visible because new version has published
                            key_list.remove(color_string)
                            key_list.append(norm_string)
            if key_list:
                for item in key_list:
                    fzf.append_fzf(item + "\n")
            else:
                raise NoSelectionMade(
                    "Bucket might be empty or there was no selection made"
                )
            if multi_select:
                self.path_list = list(fzf.execute_fzf(print_col=-1, multi_select=True))
            else:
                self.path_list[0] = fzf.execute_fzf(print_col=-1)

    def get_object_version(
        self, bucket=None, key=None, delete=False, select_all=False, non_current=False
    ):
        """list object versions through fzf

        Args:
            bucket: string, if not set, class instance's bucket_name would be used
            key: string, if not set, class instance's bucket_path would be used
            delete: bool, allow to choose delete marker
            select_all: bool, skip fzf and pull all version into the return list
            non_current: bool, only put non_current versions into the list
        Returns:
            selected_versions: list, list of dict the user selected
                dict: {'Key': s3 key path, 'VersionId': s3 object id}
        """
        bucket = bucket if bucket else self.bucket_name
        key_list = []
        if key:
            key_list.append(key)
        else:
            key_list.extend(self.path_list)
        selected_versions = []
        for key in key_list:
            version_list = []
            paginator = self.client.get_paginator("list_object_versions")
            for result in paginator.paginate(Bucket=bucket, Prefix=key):
                for version in result.get("Versions", []):
                    if (non_current and not version.get("IsLatest")) or not non_current:
                        version_list.append(
                            {
                                "VersionId": version.get("VersionId"),
                                "Key": version.get("Key"),
                                "IsLatest": version.get("IsLatest"),
                                "DeleteMarker": False,
                                "LastModified": version.get("LastModified"),
                            }
                        )
                if delete:
                    for marker in result.get("DeleteMarkers", []):
                        version_list.append(
                            {
                                "VersionId": marker.get("VersionId"),
                                "Key": marker.get("Key"),
                                "IsLatest": marker.get("IsLatest"),
                                "DeleteMarker": True,
                                "LastModified": marker.get("LastModified"),
                            }
                        )
            if not select_all:
                fzf = Pyfzf()
                fzf.process_list(
                    version_list,
                    "VersionId",
                    "Key",
                    "IsLatest",
                    "DeleteMarker",
                    "LastModified",
                )
                if delete:
                    for result in fzf.execute_fzf(multi_select=True):
                        selected_versions.append({"Key": key, "VersionId": result})
                else:
                    selected_versions.append(
                        {"Key": key, "VersionId": fzf.execute_fzf()}
                    )
            else:
                selected_versions.extend(
                    [
                        {"Key": key, "VersionId": version.get("VersionId")}
                        for version in version_list
                    ]
                )
        return selected_versions

    def get_object_data(self, file_type=None):
        """read the s3 object

        read the s3 object file and if is yaml/json file_type, load the file into dict
        currently is only used for cloudformation

        Args:
            file_type: string, yaml/json, if specified, will load the file into dict
        """
        s3_object = self.resource.Object(self.bucket_name, self.path_list[0])
        body = s3_object.get()["Body"].read()
        body = str(body, "utf-8")
        body_dict = {}
        if file_type == "yaml":
            body_dict = process_yaml_body(body)
        elif file_type == "json":
            body_dict = process_json_body(body)
        return body_dict

    def get_object_url(self, version=None):
        # type: (str) -> str
        """return the object url of the current selected object

        :param version: get url for versioned object
        :type version: str, optional
        """
        response = self.client.get_bucket_location(Bucket=self.bucket_name)
        bucket_location = response["LocationConstraint"]
        if not version:
            return "https://s3-%s.amazonaws.com/%s/%s" % (
                bucket_location,
                self.bucket_name,
                self.path_list[0],
            )
        else:
            return "https://s3-%s.amazonaws.com/%s/%s?versionId=%s" % (
                bucket_location,
                self.bucket_name,
                self.path_list[0],
                version,
            )

    def get_s3_destination_key(self, local_path, recursive=False):
        """set the s3 key for upload destination

        check if the current s3 path ends with '/'
        if not, pass, since is already a valid path
        if yes, append the local file name to the s3 path as the key

        if recursive is set, append '/' to last if '/' does not exist

        Args:
            local_path: string, local file path
            recursive: bool, recursive operation
        """
        if recursive:
            if not self.path_list[0]:
                return local_path
            elif self.path_list[0][-1] != "/":
                return self.path_list[0] + "/" + local_path
            else:
                return self.path_list[0] + local_path
        else:
            if not self.path_list[0]:
                # if operation is at root level, return the file name
                return local_path.split("/")[-1]
            elif self.path_list[0][-1] == "/":
                # if specified s3 path, append the file name
                key = local_path.split("/")[-1]
                return self.path_list[0] + key
            else:
                return self.path_list[0]

    def _validate_input_path(self, user_input):
        """validate if the user input path is valid format"""
        accesspoint_pattern = r"^(arn:aws.*:s3:[a-z\-0-9]+:[0-9]{12}:accesspoint[/:][a-zA-Z0-9\-]{1,63}/)(.*)$"
        path_pattern = r"^(?!arn:.*)(.*/)+.*$"
        if re.match(accesspoint_pattern, user_input):
            return ("accesspoint", re.match(accesspoint_pattern, user_input).groups())
        elif re.match(path_pattern, user_input):
            return ("bucketpath", re.match(path_pattern, user_input).groups())
        else:
            return (None, None)

    def _get_path_option(self):
        """pop up fzf for user to select what to do with the path"""
        fzf = Pyfzf()
        fzf.append_fzf("root: operate on the root level of the bucket\n")
        fzf.append_fzf("interactively: interactively select a path through s3\n")
        fzf.append_fzf("input: manully input the path/name\n")
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
