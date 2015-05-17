var grid_layout = { "widgets" : [] }
var ptz_drag = false;
var ptz_camnum = 0;
var ptz_drag_x = 0;
var ptz_drag_y = 0;
var ptz_moves = 0;
var ptz_direction = -1;
var ptz_accel = 1;
var ptz_mousedown_ev = null;
var ptz_mousemove_ev = null;
var ptz_mouseup_ev = null;



function gridster_drag_save()
{
    var $ =jQuery.noConflict();

    var s = gridster.serialize();
    for (a=0;a<grid_layout.widgets.length;a++)
    {
        grid_layout.widgets[a].col = s[a].col;
        grid_layout.widgets[a].row = s[a].row;
    }
    grid_data = JSON.stringify(grid_layout);
    if (grid_data)
    {
        $.ajax("/video/grid_layout_set/", {
                method: "POST",
                data: grid_data,
                success: function(data) {
            },
        });
    }
}



function widget_resup(camnum)
{
    if (grid_layout.widgets[camnum].w<4)
    {
        grid_layout.widgets[camnum].w++;
        grid_layout.widgets[camnum].h++;
    }
    aspect =  grid_layout.widgets[camnum].w
    gridster.resize_widget(gridster.$widgets.eq(camnum),grid_layout.widgets[camnum].w,grid_layout.widgets[camnum].h);

    if (document.getElementById('camera_'+camnum).src !="")
    {
        document.getElementById('camera_'+camnum).src = document.getElementById('camera_'+camnum).src.replace("aspect=","token2=") + "&aspect="+aspect;
    }
    gridster_drag_save()
}

function widget_resdown(camnum)
{
    if (grid_layout.widgets[camnum].w>1)
    {
        grid_layout.widgets[camnum].w--;
        grid_layout.widgets[camnum].h--;
    }
    aspect =  grid_layout.widgets[camnum].w
    gridster.resize_widget(gridster.$widgets.eq(camnum),grid_layout.widgets[camnum].w,grid_layout.widgets[camnum].h);

    if (document.getElementById('camera_'+camnum).src !="")
    {
        document.getElementById('camera_'+camnum).src = document.getElementById('camera_'+camnum).src.replace("aspect=","token2=") + "&aspect="+aspect;
    }
    gridster_drag_save()
}








function camera_dialog(camnum)
{
    var $ =jQuery.noConflict();

    $.ajax("/video/get_sinks", {
        success: function(data) {
            sinks = JSON.parse(data);
            $("#camdialog select").empty();
            $("#camdialog select").append('<option value=-1>Select...</option>');
            $("#camdialog select").append('<option value=-2>None</option>');
            for (a=0;a<sinks.names.length;a++)
            {
                $("#camdialog select").append('<option value='+a+'>'+sinks.names[a]+'</option>');
            }


            $("#camdialog select").change(function(){
                var value = $(this).val();
                $("#camdialog").dialog("close");
                if (value>=0)
                {
                    // URL!!!
                    document.getElementById('camera_'+camnum).src = "http://localhost:8090/"+sinks.names[value]+".mjpg?token="+Math.random()+"&aspect="+grid_layout.widgets[camnum].w;
                    $("#camdialog select").off();

                    grid_layout.widgets[camnum].sink = sinks.names[value];

                    grid_data = JSON.stringify(grid_layout);
                    $.ajax("/video/grid_layout_set/", {
                        method: "POST",
                        data: grid_data,
                        success: function(data) {
                        },
                    });
                }
                else
                {
                    // URL!!!
                    document.getElementById('camera_'+camnum).src = "";
                    $("#camdialog select").off();
                    grid_layout.widgets[camnum].sink = "";
                    grid_data = JSON.stringify(grid_layout);
                    $.ajax("/video/grid_layout_set/", {
                        method: "POST",
                        data: grid_data,
                        success: function(data) {
                        },
                    });
                }
            });


            $("#camdialog").dialog({modal: false, height: 130, width:250, position:{ my: "center", at: "center", of: '#controls_'+camnum }});
        },
    });
}



function pantilt_startdrag(e)
{
    ptz_moves = 0;
    ptz_direction = -1;
    ptz_accel = 1;
    ptz_drag = true;
    ptz_drag_x = e.clientX;
    ptz_drag_y = e.clientY;

}

function pantilt_stopdrag(e)
{
    var $ =jQuery.noConflict();

    if (ptz_drag)
    {
        ptz_drag = false;
        cx = e.clientX;
        cy = e.clientY;
        deltax = cx - ptz_drag_x;
        deltay = cy - ptz_drag_y;

        angle = ((Math.atan2(deltay,deltax)) * (180/Math.PI));

        if ((cx>=ptz_drag_x) && (cy<=ptz_drag_y))
            angle = angle+90;
        else if ((cx>=ptz_drag_x) && (cy>=ptz_drag_y))
            angle = angle+90;
        else if ((cx<=ptz_drag_x) && (cy>=ptz_drag_y))
        {
            angle+=90;
        }
        else if ((cx<=ptz_drag_x) && (cy<=ptz_drag_y))
        {
            angle = -angle;
            angle = 180-angle;
            angle +=270;
        }


        if ((angle>(360-22.5)) || (angle<(22.5)))
        {
            if (ptz_direction==0)
                ptz_accel++;
            else
                ptz_accel = 1
            ptz_direction = 0;
            $.ajax("/video/cam_pan_up?src=" + encodeURIComponent(grid_layout.widgets[ptz_camnum].sink) + "&srctype=sink&step="+ptz_accel, {
                success: function(data) {
                },
            });
        }
        else if ((angle>=(22.5)) && (angle<=(22.5+45)))
        {
            if (ptz_direction==1)
                ptz_accel++;
            else
                ptz_accel = 1
            ptz_direction = 1;
            $.ajax("/video/cam_pan_up_right?src=" + encodeURIComponent(grid_layout.widgets[ptz_camnum].sink) + "&srctype=sink&step="+ptz_accel, {
                success: function(data) {
                },
            });
        }
        else if ((angle>=(22.5+45)) && (angle<=(22.5+90)))
        {
            if (ptz_direction==2)
                ptz_accel++;
            else
                ptz_accel = 1
            ptz_direction = 2;
            $.ajax("/video/cam_pan_right?src=" + encodeURIComponent(grid_layout.widgets[ptz_camnum].sink) + "&srctype=sink&step="+ptz_accel, {
                success: function(data) {
                },
            });
        }
        else if ((angle>=(22.5+90)) && (angle<=(22.5+135)))
        {
            if (ptz_direction==3)
                ptz_accel++;
            else
                ptz_accel = 1
            ptz_direction = 3;
            $.ajax("/video/cam_pan_bottom_right?src=" + encodeURIComponent(grid_layout.widgets[ptz_camnum].sink) + "&srctype=sink&step="+ptz_accel, {
                success: function(data) {
                },
            });
        }
        else if ((angle>=(22.5+135)) && (angle<=(22.5+180)))
        {
            if (ptz_direction==4)
                ptz_accel++;
            else
                ptz_accel = 1
            ptz_direction = 4;
            $.ajax("/video/cam_pan_bottom?src=" + encodeURIComponent(grid_layout.widgets[ptz_camnum].sink) + "&srctype=sink&step="+ptz_accel, {
                success: function(data) {
                },
            });
        }

        else if ((angle>=(22.5+180)) && (angle<=(22.5+225)))
        {
            if (ptz_direction==5)
                ptz_accel++;
            else
                ptz_accel = 1
            ptz_direction = 5;
            $.ajax("/video/cam_pan_bottom_left?src=" + encodeURIComponent(grid_layout.widgets[ptz_camnum].sink) + "&srctype=sink&step="+ptz_accel, {
                success: function(data) {
                },
            });
        }

        else if ((angle>=(22.5+225)) && (angle<=(22.5+270)))
        {
            if (ptz_direction==6)
                ptz_accel++;
            else
                ptz_accel = 1
            ptz_direction = 6;
            $.ajax("/video/cam_pan_left?src=" + encodeURIComponent(grid_layout.widgets[ptz_camnum].sink) + "&srctype=sink&step="+ptz_accel, {
                success: function(data) {
                },
            });
        }
        else
        {
            if (ptz_direction==7)
                ptz_accel++;
            else
                ptz_accel = 1
            ptz_direction = 7;
            $.ajax("/video/cam_pan_up_left?src=" + encodeURIComponent(grid_layout.widgets[ptz_camnum].sink) + "&srctype=sink&step="+ptz_accel, {
                success: function(data) {
                },
            });
        }
    }
}


function pantilt_calcdrag(e)
{
    ptz_moves++;
    if (((ptz_moves%5)==0) && (ptz_drag))
    {
        pantilt_stopdrag(e);
        ptz_drag = true;
    }
}


function pantilt_dialog(camnum)
{
    var $ =jQuery.noConflict();
    $("#pantiltdialog").dialog({modal: false, height:532, width:662, position:{ my: "center bottom", at: "center center", of: window }});
    document.getElementById('pantilt_img').src = document.getElementById('camera_'+camnum).src.replace("aspect=","token2=");
    ptz_camnum = camnum;
    if (ptz_mousedown_ev)
        document.getElementById('pantilt_img').removeEventListener('mousedown', pantilt_startdrag);
    if (ptz_mousemove_ev)
        document.getElementById('pantilt_img').removeEventListener('mousemove', pantilt_calcdrag);
    if (ptz_mouseup_ev)
        document.getElementById('pantilt_img').removeEventListener('mouseup', pantilt_stopdrag);

    document.getElementById('pantilt_img').addEventListener('mousedown', pantilt_startdrag, false);
    document.getElementById('pantilt_img').addEventListener('mousemove', pantilt_calcdrag, false);
    document.getElementById('pantilt_img').addEventListener('mouseup', pantilt_stopdrag, false);

    ptz_mousedown_ev = pantilt_startdrag;
    ptz_mousemove_ev = pantilt_calcdrag;
    ptz_mouseup_ev = pantilt_stopdrag;

}





function display_controls(num)
{
    document.getElementById("controls_" + num).style.display="block";
}

function hide_controls(num)
{
    document.getElementById("controls_" + num).style.display="none";
}



function get_widget(num)
{
    if (typeof grid_layout.widgets[num] !== 'undefined')
    {
        widget = grid_layout.widgets[num];
        h = widget.h;
        w = widget.w;
        sink = widget.sink;
    }
    else
    {
        h = w = 1;
        sink = "";
    }
    str = "";


    if (sink!="")
    {
        str += "<div style='z-index:1' onmouseover='display_controls("+num+")' onmouseout='hide_controls("+num+")' height='100%' width='100%' >";
        str += "<img style='-moz-force-broken-image-icon: 0;' alt='' onerror='if (this.naturalWidth==0) this.src=transimg' src='http://localhost:8090/" + sink + ".mjpg?token="+Math.random()+"&aspect="+w+"' id='camera_"+num+"'></img>";
        str += "<div id='controls_" + num + "' style='z-index:2;display:none;position:absolute;top:5px;left:10px;height=50px;width=50px;opacity:0.5;background-color:#666666;border-radius:5px;top:20px;'>";
        str += "&nbsp;&nbsp;"
        str += "<i class='fa fa-video-camera fa-2x fa-inverse' onclick='camera_dialog("+num+")'></i>&nbsp;&nbsp;"; 
        str += "<i class='fa fa-arrows fa-2x fa-inverse' onclick='pantilt_dialog("+num+")'></i>&nbsp;&nbsp;"; 
        str += "<i class='fa fa-plus fa-2x fa-inverse' onclick='widget_resup("+num+")'></i>&nbsp;&nbsp;"; 
        str += "<i class='fa fa-minus fa-2x fa-inverse' onclick='widget_resdown("+num+")'></i>&nbsp;&nbsp;"; 
        str += "</div>";
        str += "</div>";
    }
    else
    {
        str += "<div style='z-index:1' onmouseover='display_controls("+num+")' onmouseout='hide_controls("+num+")' height='100%' width='100%' >";
        str += "<img style='-moz-force-broken-image-icon: 0;' alt='' onerror='if (this.naturalWidth==0) this.src=transimg' src='' id='camera_"+num+"'></img>";
        str += "<div id='controls_" + num + "' style='z-index:2;display:none;position:absolute;top:5px;left:10px;height=50px;width=50px;opacity:0.5;background-color:#666666;border-radius:5px;top:20px;'>";
        str += "&nbsp;&nbsp;"
        str += "<i class='fa fa-video-camera fa-2x fa-inverse' onclick='camera_dialog("+num+")'></i>&nbsp;&nbsp;"; 
        str += "<i class='fa fa-arrows fa-2x fa-inverse' onclick='pantilt_dialog("+num+")'></i>&nbsp;&nbsp;"; 
        str += "<i class='fa fa-plus fa-2x fa-inverse' onclick='widget_resup("+num+")'></i>&nbsp;&nbsp;"; 
        str += "<i class='fa fa-minus fa-2x fa-inverse' onclick='widget_resdown("+num+")'></i>&nbsp;&nbsp;"; 
        str += "</div>";
        str += "</div>";
    }

    return str;
}


function load_widgets()
{
    $.ajax("/video/grid_layout_get", {
        success: function(data) {
            grid_layout = JSON.parse(data);
            widgets = [];
            for (a=0;a<grid_layout.widgets.length;a++)
            {
                body = [get_widget(a), grid_layout.widgets[a].w, grid_layout.widgets[a].h,grid_layout.widgets[a].col, grid_layout.widgets[a].row];
                widgets.push(body);
            }
            $.each(widgets, function(i, widget) 
            {
                gridster.add_widget.apply(gridster, widget);
            });
        },
    });

}

