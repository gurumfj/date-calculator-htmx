from __future__ import annotations

from unittest.mock import Mock
from cleansales_backend.commands.upload_commands import UploadFileCommand


class TestUploadFileCommand:
    def test_create_upload_command_with_file_only(self) -> None:
        mock_file = Mock()
        mock_file.filename = "test.xlsx"
        
        command = UploadFileCommand(file=mock_file)
        
        assert command.file == mock_file
        assert command.metadata is None
    
    def test_create_upload_command_with_metadata(self) -> None:
        mock_file = Mock()
        mock_file.filename = "test.xlsx"
        metadata = {"user_id": "123", "source": "web"}
        
        command = UploadFileCommand(file=mock_file, metadata=metadata)
        
        assert command.file == mock_file
        assert command.metadata == metadata
        assert command.metadata is not None
        assert command.metadata["user_id"] == "123"
        assert command.metadata["source"] == "web"
    
    def test_create_upload_command_with_empty_metadata(self) -> None:
        mock_file = Mock()
        mock_file.filename = "test.xlsx"
        metadata = {}
        
        command = UploadFileCommand(file=mock_file, metadata=metadata)
        
        assert command.file == mock_file
        assert command.metadata == {}
    
    def test_upload_command_is_dataclass(self) -> None:
        # 驗證UploadFileCommand是一個dataclass
        mock_file = Mock()
        command = UploadFileCommand(file=mock_file)
        
        # dataclass應該有__dataclass_fields__屬性
        assert hasattr(command, '__dataclass_fields__')
        assert 'file' in command.__dataclass_fields__
        assert 'metadata' in command.__dataclass_fields__