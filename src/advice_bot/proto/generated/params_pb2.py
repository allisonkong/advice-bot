# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: params.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0cparams.proto\">\n\x0b\x43hannelList\x12\x14\n\x0c\x61ll_channels\x18\x01 \x01(\x08\x12\x19\n\x11specific_channels\x18\x02 \x03(\x03\"J\n\rCommandConfig\x12\x19\n\x07\x63ommand\x18\x01 \x01(\x0e\x32\x08.Command\x12\x1e\n\x08\x63hannels\x18\x02 \x01(\x0b\x32\x0c.ChannelList\"B\n\x0cServerConfig\x12\x10\n\x08guild_id\x18\x01 \x01(\x03\x12 \n\x08\x63ommands\x18\x02 \x03(\x0b\x32\x0e.CommandConfig\"(\n\x06\x43onfig\x12\x1e\n\x07servers\x18\x01 \x03(\x0b\x32\r.ServerConfig\"\x88\x01\n\rDiscordParams\x12\x1e\n\x16\x64iscord_application_id\x18\x01 \x01(\t\x12\x1a\n\x12\x64iscord_public_key\x18\x02 \x01(\t\x12\x1d\n\x15\x64iscord_client_secret\x18\x03 \x01(\t\x12\x1c\n\x14\x64iscord_secret_token\x18\x04 \x01(\t\"\x8f\x01\n\x0bMysqlParams\x12\x0c\n\x04host\x18\x01 \x01(\t\x12\x0c\n\x04user\x18\x02 \x01(\t\x12\x10\n\x08password\x18\x03 \x01(\t\x12\x10\n\x08\x64\x61tabase\x18\x04 \x01(\t\x12\x13\n\x0bssl_ca_file\x18\x05 \x01(\t\x12\x15\n\rssl_cert_file\x18\x06 \x01(\t\x12\x14\n\x0cssl_key_file\x18\x07 \x01(\t\"m\n\x06Params\x12&\n\x0e\x64iscord_params\x18\x01 \x01(\x0b\x32\x0e.DiscordParams\x12\"\n\x0cmysql_params\x18\x02 \x01(\x0b\x32\x0c.MysqlParams\x12\x17\n\x06\x63onfig\x18\x03 \x01(\x0b\x32\x07.Config\"}\n\tParamsMap\x12\x32\n\x0c\x65nvironments\x18\x01 \x03(\x0b\x32\x1c.ParamsMap.EnvironmentsEntry\x1a<\n\x11\x45nvironmentsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\x16\n\x05value\x18\x02 \x01(\x0b\x32\x07.Params:\x02\x38\x01*;\n\x07\x43ommand\x12\x13\n\x0fUNKNOWN_COMMAND\x10\x01\x12\x1b\n\x17MONTHLY_LOTTERY_COMMAND\x10\x02')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'params_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _PARAMSMAP_ENVIRONMENTSENTRY._options = None
  _PARAMSMAP_ENVIRONMENTSENTRY._serialized_options = b'8\001'
  _COMMAND._serialized_start=789
  _COMMAND._serialized_end=848
  _CHANNELLIST._serialized_start=16
  _CHANNELLIST._serialized_end=78
  _COMMANDCONFIG._serialized_start=80
  _COMMANDCONFIG._serialized_end=154
  _SERVERCONFIG._serialized_start=156
  _SERVERCONFIG._serialized_end=222
  _CONFIG._serialized_start=224
  _CONFIG._serialized_end=264
  _DISCORDPARAMS._serialized_start=267
  _DISCORDPARAMS._serialized_end=403
  _MYSQLPARAMS._serialized_start=406
  _MYSQLPARAMS._serialized_end=549
  _PARAMS._serialized_start=551
  _PARAMS._serialized_end=660
  _PARAMSMAP._serialized_start=662
  _PARAMSMAP._serialized_end=787
  _PARAMSMAP_ENVIRONMENTSENTRY._serialized_start=727
  _PARAMSMAP_ENVIRONMENTSENTRY._serialized_end=787
# @@protoc_insertion_point(module_scope)
