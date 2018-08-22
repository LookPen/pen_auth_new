layui.use(['layer', 'table', 'carousel'], function () {

    var layer = layui.layer//弹层
    var table = layui.table//表格
    var carousel = layui.carousel//轮播

    layer.msg('欢迎使用 pen_auth');

    //轮播
    carousel.render({
        elem: '#head_car',
        width: '100%',
        height: 200,
        arrow: 'none',
        anim: 'fade'
    });

    //客户端列表数据
    table.render({
        elem: '#app_list',
        height: 332,
        url: '/o/api/app_list',
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

    //监听客户端列表数据工具条
    table.on('tool(applications)', function (obj) {
        var $ = layui.$

        var data = obj.data
        var layEvent = obj.event;
        var layID = $(this).attr('lay-id')

        if (layEvent === 'detail') {
            layer.msg(layID)
        }
        else if (layEvent === 'del') {
            layer.confirm('删除该客户端后,该客户端产生的token相关数据将清除！', function (index) {
                obj.del();
                layer.close(index);
            });
        } else if (layEvent === 'edit') {
            layer.msg('编辑操作');
        }
    });
})