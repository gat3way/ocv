/* 
    Handle Camera / URL dynamic stuff
*/
var select = document.getElementById('id_device');
var urlbox = document.getElementById('id_url');
var canvas = document.getElementById('zone_canvas');
var exclude_input = document.getElementById('id_motion_exclude');
var ctx = canvas.getContext('2d');
ctx.fillStyle="rgba(255, 0, 0, 0.25)";
var drag = false;
var rect = {};

exclude_input.value = decodeURI(exclude_input.value);
if (isEmpty(exclude_input.value))
{
    exclude_input.value = '{ "rects" : [] }';
}
rects = JSON.parse(exclude_input.value);
var background = new Image();
background.src = "/video/get_image?url="+encodeURIComponent(urlbox.value);
background.onload = draw_bg





function change_device(name)
{
    name = select.options[select.selectedIndex].innerHTML;
    xmlhttp = new XMLHttpRequest();
    xmlhttp.onreadystatechange = function() {
        if (xmlhttp.readyState == 4 ) {
           if(xmlhttp.status == 200){
               document.getElementById('id_url').value = xmlhttp.responseText;
           }
        }
    }
    xmlhttp.open("GET", "/video/get_url/?src="+name, true);
    xmlhttp.send();
}



function isEmpty(str) {
    return (!str || 0 === str.length);
}





function draw_bg()
{
    ctx.drawImage(background,0,0);
    ctx.fillStyle="rgba(0, 0, 0, 1)";

    sz = document.getElementById("id_top_blank_pixels").value;
    ctx.fillRect(0, 0, 640, sz);
    sz = document.getElementById("id_bottom_blank_pixels").value;
    ctx.fillRect(0, 480-sz, 640, 480);
    sz = document.getElementById("id_left_blank_pixels").value;
    ctx.fillRect(0, 0, sz, 480);
    sz = document.getElementById("id_right_blank_pixels").value;
    ctx.fillRect(640-sz, 0, 640, 480);

    ctx.fillStyle="rgba(255, 0, 0, 0.25)";

    rs = rects.rects
    for (var i in rs)
    {
        ctx.fillRect(rs[i].x, rs[i].y, rs[i].w, rs[i].h);
    }
}





function draw() 
{
    ctx.fillRect(rect.startX, rect.startY, rect.w, rect.h);
}

function mouseDown(e)
{
    if (e.which < 2)
    {
        rect.startX = e.pageX - this.offsetLeft;
        rect.startY = e.pageY - this.offsetTop;
        drag = true;
    }
}


function mouseUp(e) 
{
    if (e.which < 2)
    {
        drag = false;
        if (rect.h && rect.w)
        {
            obj = { x : parseInt(rect.startX), y: parseInt(rect.startY), h: parseInt(rect.h), w : parseInt(rect.w) }
            rs = rects.rects;
            rs.push(obj);
        }
        exclude_input.value = JSON.stringify(rects);
    }
}


function mouseMove(e) {
    if (drag) 
    {
        rect.w = (e.pageX - this.offsetLeft) - rect.startX;
        rect.h = (e.pageY - this.offsetTop) - rect.startY ;
        draw_bg()
        draw();
    }
}


function mouseRight(e) {
    e.preventDefault();
    exclude_input.value = '{ "rects" : [] }';
    rects = JSON.parse(exclude_input.value);
    drag = false;
    draw_bg()
    return false;
}





function change_url()
{
    select.selectedIndex = 0;
    background.src = "/video/get_image?url="+encodeURIComponent(urlbox.value);
    draw_bg()
}

function change_url2()
{
    select.selectedIndex = 0;
}





select.onchange = change_device;
urlbox.onchange = change_url;
urlbox.onkeyup = change_url2;
urlbox.onkeydown = change_url2;
urlbox.onkeypress = change_url2;
canvas.oncontextmenu = mouseRight;
canvas.addEventListener('mousedown', mouseDown, false);
canvas.addEventListener('mouseup', mouseUp, false);
canvas.addEventListener('mousemove', mouseMove, false);
document.getElementById("id_top_blank_pixels").onchange = draw_bg;
document.getElementById("id_bottom_blank_pixels").onchange = draw_bg;
document.getElementById("id_left_blank_pixels").onchange = draw_bg;
document.getElementById("id_right_blank_pixels").onchange = draw_bg;
document.getElementById("id_top_blank_pixels").onkeypress = draw_bg;
document.getElementById("id_bottom_blank_pixels").onkeypress = draw_bg;
document.getElementById("id_left_blank_pixels").onkeypress = draw_bg;
document.getElementById("id_right_blank_pixels").onkeypress = draw_bg;
document.getElementById("id_top_blank_pixels").onkeydown = draw_bg;
document.getElementById("id_bottom_blank_pixels").onkeydown = draw_bg;
document.getElementById("id_left_blank_pixels").onkeydown = draw_bg;
document.getElementById("id_right_blank_pixels").onkeydown = draw_bg;
document.getElementById("id_top_blank_pixels").onkeyup = draw_bg;
document.getElementById("id_bottom_blank_pixels").onkeyup = draw_bg;
document.getElementById("id_left_blank_pixels").onkeyup = draw_bg;
document.getElementById("id_right_blank_pixels").onkeyup = draw_bg;
//document.getElementById("camcontainer").onmouseup = mouseup;
