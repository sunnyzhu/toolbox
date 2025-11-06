from pyecharts.charts import Map
from pyecharts import options as opts
from pyecharts.globals import CurrentConfig

# 强制使用在线资源（解决地图文件缺失问题）
# CurrentConfig.ONLINE_HOST = "https://cdn.jsdelivr.net/npm/echarts@5.4.3/dist/"

# 您的数据（确保省份名称与PyEcharts标准一致）
data = [
    ("北京市", 7), ("天津市", 5), ("河北省", 6), ("山西省", 4), ("内蒙古自治区", 3),
    ("辽宁省", 6), ("吉林省", 4), ("黑龙江省", 5), ("上海市", 2), ("江苏省", 2),
    ("浙江省", 4), ("安徽省", 5), ("福建省", 3), ("江西省", 4), ("山东省", 6),
    ("河南省", 5), ("湖北省", 4), ("湖南省", 5), ("广东省", 4), ("广西壮族自治区", 3),
    ("海南省", 3), ("重庆市", 4), ("四川省", 8), ("贵州省", 2), ("云南省", 2),
    ("陕西省", 3), ("甘肃省", 2), ("青海省", 2), ("宁夏回族自治区", 2), ("新疆维吾尔自治区", 4),
    ("西藏自治区", 0),("台湾省", 0),("香港特别行政区", 0),("澳门特别行政区", 0)
]

# 创建地图对象
c = (
    Map(init_opts=opts.InitOpts(width="2000px", height="1200px"))  # 设置画布大小
    .add(
        series_name="数值",
        data_pair=data,
        maptype="china",
        is_map_symbol_show=False,  # 隐藏默认标记点
        label_opts=opts.LabelOpts(
            is_show=True,
            color="#000",  # 标签颜色
            font_size=12,
            formatter="{b}\n{c}"  # 换行显示名称和数值
        ),
        itemstyle_opts=opts.ItemStyleOpts(border_color="#fff")  # 区域边框颜色
    )
    .set_global_opts(
        title_opts=opts.TitleOpts(title="中国各省数值分布（颜色深浅=数值大小）"),
        visualmap_opts=opts.VisualMapOpts(
            min_=2,
            max_=8,
            is_piecewise=False,  # 连续型渐变
            range_color=["#E6F2FF", "#1A8CFF", "#0059b3"],  # 蓝渐变
            is_calculable=True,  # 显示拖动条
            pos_left="10%",  # 控制组件位置
        ),
        tooltip_opts=opts.TooltipOpts(trigger="item", formatter="{b}: {c}")
    )
)

# 输出文件
c.render("china_map.html")
print("已生成修正版地图，请用浏览器打开 china_map_fixed.html")