layui.use(['layer', 'table', 'carousel', 'form'], function () {

    var layer = layui.layer//弹层
    var table = layui.table//表格
    var carousel = layui.carousel//轮播
    var form = layui.form//表单

    //首页加载
    say_hi(layer, carousel);

    //绑定客户端列表
    bind_app_list(table)

    //监听客户端列表数据工具条
    bind_app_list_tool(layer, table, form)

})

//首页加载
function say_hi(layer, carousel) {
    layer.msg('欢迎使用 pen_auth');
    carousel.render({
        elem: '#head_car',
        width: '100%',
        height: 200,
        arrow: 'none',
        anim: 'fade'
    });
}

//绑定客户端列表
function bind_app_list(table) {
    table.render({
        elem: '#apps',
        height: 332,
        url: '/o/api/app',
        page: true,
        cols: [[
            {field: 'client_id', title: '客户端id', width: 180, sort: true, fixed: 'left'},
            {field: 'client_name', title: '客户端名称', width: 180, sort: true, fixed: 'left'},
            {field: 'client_type', title: '类型', width: 180},
            {field: 'authorization_grant_type', title: '授权类型', width: 180, sort: true},
            {field: 'remark', title: '说明'},
            {fixed: 'right', width: 165, align: 'center', toolbar: '#app_action'}
        ]]
    });
}

//监听客户端列表数据工具条
function bind_app_list_tool(layer, table, form) {
    table.on('tool(applications)', function (obj) {
        var $ = layui.$
        var layEvent = obj.event;
        var layID = $(this).attr('lay-id')

        if (layEvent === 'detail') {
            app_detail(layer, form, false)
        }
        else if (layEvent === 'del') {
            layer.confirm('删除该客户端后,该客户端产生的token相关数据将清除！', function (index) {
                obj.del();
                layer.close(index);
            });
        }
        else if (layEvent === 'edit') {
            layer_index = app_detail(layer, form, true)
            app_valid_form(form)
            app_update(layer, form, table, layer_index)
        }
    });
}

//弹窗显示客户端详情
function app_detail(layer, form, show_save) {
    $ = layui.$

    $.get('/o/api/app', {'client_id': 1}, function (data, status) {
        form.val('app_info', {
            "client_name": data.client_name,
            "client_id": data.client_id,
            "client_secret": data.client_secret,
            "client_type": data.client_type,
            "authorization_grant_type": data.authorization_grant_type,
            "skip_authorization": data.skip_authorization,
            "redirect_uris": data.redirect_uris,
            "remark": data.remark
        })
    }, 'json');

    layer_index = layer.open({
        type: 1,
        title: '客户端详情',
        area: ['680px', '400px'],
        content: $('#app_detail')
    });

    $('#app_detail').removeClass('layui-hide')

    if (show_save) {
        $('#save_app').removeClass('layui-hide')
    }
    else {
        $('#save_app').addClass('layui-hide')
    }

    return layer_index
}

//弹窗编辑客户端
function app_update(layer, form, table, layer_index) {

    form.on('submit(save_app)', function (data) {

        $.ajax({
            url: "/o/api/app",
            data: data.field,
            type: "POST",
            dataType: 'json',
            success: function (data) {
                layer.msg('保存成功')
                layer.close(layer_index)
                bind_app_list(table)
            },
            error: function (er) {
                if (er.status != 500)
                    layer.msg(er.responseText)
                else
                    layer.msg('系统错误')
            }
        });

        return false;
    });
}

//验证客户端表单
function app_valid_form(form) {
    form.verify({
        client_name: function (value) {
            if (value.length <= 0) {
                return '客户端名称不能为空';
            }
        }
    });
}
