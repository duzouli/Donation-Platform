'''
开发设计思路:

我们在管理后台(admin)单个添加和或csv批量导入的，称之为 后台添加
用户自己递交的，称之为 人工添加
用户递交信息时，根据区分字段查询出的数据 称之为 已存在数据

[列说明: 数据是谁添加的  数据核实状态  递交请求处理方案]
[递交请求处理方案: 查询出的已存在数据如何处理, 提交的数据如何处理]

(医疗)机构递交请求(区分: 省 + 市 + 名称)
    后台添加        已核实  删除, 创建
    后台添加        未核实  删除, 创建
    人工添加(本人)  已核实  更新(合并联系人、合并需求)
    人工添加(本人)  未核实  删除, 创建
    人工添加(他人)  已核实  ?(暂未处理, 丢弃数据)
    人工添加(他人)  未核实  ?(暂未处理, 丢弃数据)

(爱心)团队递交请求(区分： 名称)
    本人添加  已核实  更新(合并联系人)
    本人添加  未核实  删除, 创建
    他人添加  已核实  ?(暂未处理, 丢弃数据)
    他人添加  未核实  ?(暂未处理, 丢弃数据)
'''
from rest_framework import serializers
from filer.models.imagemodels import Image

from .models import Organization, OrganizationContact, OrganizationDemand, Team, TeamContact
from registration.models import User
from .cache_helper import clear_by_prefix


class ImageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Image
        fields = ['url', 'id', 'folder', 'file', 'label', 'original_filename', 'size', 'width', 'height', 'uploaded_at']
        extra_kwargs = {
            'id': {'required': False},
            'url': {'required': False, 'read_only': True},
            'size': {'required': False, 'read_only': True},
            'width': {'required': False, 'read_only': True},
            'height': {'required': False, 'read_only': True},
            'uploaded_at': {'required': False, 'read_only': True},
        }

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['url', 'phone', 'id']
        extra_kwargs = {
            'id': {'required': False},
            'url': {'required': False, 'read_only': True},
        }

class OrganizationContactSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OrganizationContact
        fields = ['url', 'id', 'organization', 'name', 'phone', 'add_time',]
        extra_kwargs = {
            'id': {'required': False},
            'url': {'required': False, 'read_only': True},
            'add_time': {'required': False, 'read_only': True},
            'organization': {'required': False},
        }

    def create(self, validated_data):
        clear_by_prefix('organization')
        return super(OrganizationContactSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        clear_by_prefix('organization')
        return super(OrganizationContactSerializer, self).update(instance, validated_data)

class OrganizationDemandSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = OrganizationDemand
        fields = ['url', 'id', 'organization', 'name', 'remark', 'amount', 'receive_amount', 'add_time',]
        extra_kwargs = {
            'id': {'required': False},
            'url': {'required': False, 'read_only': True},
            'add_time': {'required': False, 'read_only': True},
            'organization': {'required': False},
            'remark': {'required': False},
            'amount': {'required': False},
            'receive_amount': {'required': False},
        }

    def create(self, validated_data):
        clear_by_prefix('organization')
        return super(OrganizationDemandSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        clear_by_prefix('organization')
        return super(OrganizationDemandSerializer, self).update(instance, validated_data)

class OrganizationSerializer(serializers.HyperlinkedModelSerializer):
    contacts = OrganizationContactSerializer(source='organizationcontact_set', many=True)
    demands = OrganizationDemandSerializer(source='organizationdemand_set', many=True)

    class Meta:
        model = Organization
        fields = ['url', 'id', 'contacts', 'demands', 'province', 'city', 'name', 'address', 'source', 'verified', 'add_time', 'is_manual', 'inspector', 'emergency']
        extra_kwargs = {
            'id': {'required': False},
            'url': {'required': False, 'read_only': True},
            'add_time': {'required': False, 'read_only': True},
            'inspector': {'required': False},
            'emergency': {'required': False},
            'address': {'required': False},
            'source': {'required': False},
            'verified': {'required': False, 'default': False},
            'is_manual': {'required': False, 'default': True},
        }

    def create(self, validated_data):
        contacts_data = validated_data.pop('organizationcontact_set', [])
        demands_data = validated_data.pop('organizationdemand_set', [])

        validated_data.pop('inspector', None)
        user = self.context['request'].user
        validated_data['inspector'] = user
        validated_data['is_manual'] = True
        validated_data['verified'] = False
        province = validated_data.pop('province', None)
        city = validated_data.pop('city', None)
        name = validated_data.pop('name', None)

        instance, created = Organization.objects.get_or_create(
            name=name,
            province=province,
            city=city,
            defaults=validated_data
        )

        is_create_related = True
        is_update_related = False
        if not created:
            # 已存在数据
            if not instance.is_manual:
                # 后台添加
                instance.delete()
            else:
                if instance.inspector == user:
                    # 本人创建
                    if instance.verified:
                        # 已验证
                        is_create_related = False
                        is_update_related = True
                        # 更新
                        for key in validated_data:
                            setattr(instance, key, validated_data[key])
                        instance.save()
                    else:
                        # 未验证
                        instance.delete()
                else:
                    # 他人创建
                    is_create_related = False
                    pass
        if is_create_related:
            # 新数据-直接添加
            if not created:
                instance = Organization.objects.create(
                    name=name,
                    province=province,
                    city=city,
                    **validated_data
                )
            for contact_data in contacts_data:
                contact_data.pop('organization', None)
                contact = OrganizationContact.objects.create(
                    organization=instance,
                    **contact_data
                )
            for demand_data in demands_data:
                demand_data.pop('organization', None)
                demand = OrganizationDemand.objects.create(
                    organization=instance,
                    **demand_data
                )
        if is_update_related:
            self.f_contacts_update(instance, contacts_data, delete_exclude=False)
            self.f_demands_update(instance, demands_data, delete_exclude=False)

        clear_by_prefix('organization')

        return instance

    def f_contacts_update(self, instance, contacts_data, delete_exclude=True):
        contact_phones = []
        for contact_data in contacts_data:
            contact_data.pop('add_time', None)
            contact_data.pop('organization', None)
            phone = contact_data.pop('phone', None)
            if bool(phone):
                contact_phones.append(phone)
                contact, contact_created = OrganizationContact.objects.update_or_create(
                    organization=instance,
                    phone=phone,
                    defaults=contact_data
                )
        
        if bool(contact_phones) and delete_exclude:
            OrganizationContact.objects.filter(organization=instance).exclude(phone__in=contact_phones).delete()

    def f_demands_update(self, instance, demands_data, delete_exclude=True):
        demand_names = []
        for demand_data in demands_data:
            demand_data.pop('add_time', None)
            demand_data.pop('organization', None)
            name = demand_data.pop('name', None)
            if bool(name):
                demand_names.append(name)
                demand, demand_created = OrganizationDemand.objects.update_or_create(
                    organization=instance,
                    name=name,
                    defaults=demand_data
                )
        
        if bool(demand_names) and delete_exclude:
            OrganizationDemand.objects.filter(organization=instance).exclude(name__in=demand_names).delete()

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if instance.inspector != user:
            return instance
        contacts_data = validated_data.pop('organizationcontact_set', [])
        demands_data = validated_data.pop('organizationdemand_set', [])
        validated_data.pop('inspector', None)
        validated_data.pop('add_time', None)

        instance = super(OrganizationSerializer, self).update(instance, validated_data)

        self.f_contacts_update(instance, contacts_data)
        self.f_demands_update(instance, demands_data)

        clear_by_prefix('organization')

        return instance 

# -----------------------------------------------------------------------------------------------------

class TeamContactSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = TeamContact
        fields = ['url', 'id', 'team', 'name', 'phone', 'add_time',]
        extra_kwargs = {
            'id': {'required': False},
            'url': {'required': False, 'read_only': True},
            'add_time': {'required': False, 'read_only': True},
            'team': {'required': False},
        }

    def create(self, validated_data):
        clear_by_prefix('team')
        return super(TeamContactSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        clear_by_prefix('team')
        return super(TeamContactSerializer, self).update(instance, validated_data)

class TeamSerializer(serializers.HyperlinkedModelSerializer):
    contacts = TeamContactSerializer(source='teamcontact_set', many=True)

    class Meta:
        model = Team
        fields = ['url', 'id', 'contacts', 'type', 'name', 'address', 'main_text', 'verified', 'inspector', 'wechat_qrcode', 'add_time',]
        extra_kwargs = {
            'id': {'required': False},
            'url': {'required': False, 'read_only': True},
            'add_time': {'required': False, 'read_only': True},
            'inspector': {'required': False},
            'wechat_qrcode': {'required': False},
        }

    def create(self, validated_data):
        contacts_data = validated_data.pop('teamcontact_set', [])

        validated_data.pop('inspector', None)
        user = self.context['request'].user
        validated_data['inspector'] = user
        name = validated_data.pop('name', None)
        validated_data['verified'] = False

        instance, created = Team.objects.get_or_create(
            name=name,
            defaults=validated_data
        )

        is_create_related = True
        is_update_related = False
        if not created:
            # 已存在数据
            if instance.inspector == user:
                # 本人创建
                if instance.verified:
                    # 已验证
                    is_create_related = False
                    is_update_related = True
                    # 更新
                    for key in validated_data:
                        setattr(instance, key, validated_data[key])
                    instance.save()
                else:
                    # 未验证
                    instance.delete()
            else:
                # 他人创建
                is_create_related = False
                pass
        
        if is_create_related:
            # 新数据-直接添加
            if not created:
                instance = Team.objects.create(
                    name=name,
                    **validated_data
                )
            for contact_data in contacts_data:
                contact_data.pop('team', None)
                contact = TeamContact.objects.create(
                    team=instance,
                    **contact_data
                )
        if is_update_related:
            self.f_contacts_update(instance, contacts_data, delete_exclude=False)

        clear_by_prefix('team')

        return instance

    def f_contacts_update(self, instance, contacts_data, delete_exclude=True):
        contact_phones = []
        for contact_data in contacts_data:
            contact_data.pop('team', None)
            phone = contact_data.pop('phone', None)
            if bool(phone):
                contact_phones.append(phone)
                contact, contact_created = TeamContact.objects.update_or_create(
                    team=instance,
                    phone=phone,
                    defaults=contact_data
                )
        
        if bool(contact_phones) and delete_exclude:
            TeamContact.objects.filter(team=instance).exclude(phone__in=contact_phones).delete()

    def update(self, instance, validated_data):
        user = self.context['request'].user
        if instance.inspector != user:
            return instance
        contacts_data = validated_data.pop('teamcontact_set', [])
        validated_data.pop('add_time', None)
        validated_data.pop('inspector', None)

        instance = super(TeamSerializer, self).update(instance, validated_data)

        self.f_contacts_update(instance, contacts_data)

        clear_by_prefix('team')

        return instance 
