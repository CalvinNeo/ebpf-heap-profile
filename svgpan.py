import os, re

SVGPAN = '''
<script type="text/ecmascript"><![CDATA[
// SVGPan
// http://www.cyberz.org/blog/2009/12/08/svgpan-a-javascript-svg-panzoomdrag-library/
// Local modification: if(true || ...) below to force panning, never moving.

/**
 *  SVGPan library 1.2
 * ====================
 *
 * Given an unique existing element with id "viewport", including the
 * the library into any SVG adds the following capabilities:
 *
 *  - Mouse panning
 *  - Mouse zooming (using the wheel)
 *  - Object dargging
 *
 * Known issues:
 *
 *  - Zooming (while panning) on Safari has still some issues
 *
 * Releases:
 *
 * 1.2, Sat Mar 20 08:42:50 GMT 2010, Zeng Xiaohui
 *	Fixed a bug with browser mouse handler interaction
 *
 * 1.1, Wed Feb  3 17:39:33 GMT 2010, Zeng Xiaohui
 *	Updated the zoom code to support the mouse wheel on Safari/Chrome
 *
 * 1.0, Andrea Leofreddi
 *	First release
 *
 * This code is licensed under the following BSD license:
 *
 * Copyright 2009-2010 Andrea Leofreddi <a.leofreddi@itcharm.com>. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without modification, are
 * permitted provided that the following conditions are met:
 *
 *    1. Redistributions of source code must retain the above copyright notice, this list of
 *       conditions and the following disclaimer.
 *
 *    2. Redistributions in binary form must reproduce the above copyright notice, this list
 *       of conditions and the following disclaimer in the documentation and/or other materials
 *       provided with the distribution.
 *
 * THIS SOFTWARE IS PROVIDED BY Andrea Leofreddi ``AS IS'' AND ANY EXPRESS OR IMPLIED
 * WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND
 * FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL Andrea Leofreddi OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
 * CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
 * ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
 * ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 *
 * The views and conclusions contained in the software and documentation are those of the
 * authors and should not be interpreted as representing official policies, either expressed
 * or implied, of Andrea Leofreddi.
 */

var root = document.documentElement;

var state = 'none', stateTarget, stateOrigin, stateTf;

setupHandlers(root);

/**
 * Register handlers
 */
function setupHandlers(root){
	setAttributes(root, {
		"onmouseup" : "add(evt)",
		"onmousedown" : "handleMouseDown(evt)",
		"onmousemove" : "handleMouseMove(evt)",
		"onmouseup" : "handleMouseUp(evt)",
		//"onmouseout" : "handleMouseUp(evt)", // Decomment this to stop the pan functionality when dragging out of the SVG element
	});

	if(navigator.userAgent.toLowerCase().indexOf('webkit') >= 0)
		window.addEventListener('mousewheel', handleMouseWheel, false); // Chrome/Safari
	else
		window.addEventListener('DOMMouseScroll', handleMouseWheel, false); // Others

	var g = svgDoc.getElementById("svg");
	g.width = "100%";
	g.height = "100%";
}

/**
 * Instance an SVGPoint object with given event coordinates.
 */
function getEventPoint(evt) {
	var p = root.createSVGPoint();

	p.x = evt.clientX;
	p.y = evt.clientY;

	return p;
}

/**
 * Sets the current transform matrix of an element.
 */
function setCTM(element, matrix) {
	var s = "matrix(" + matrix.a + "," + matrix.b + "," + matrix.c + "," + matrix.d + "," + matrix.e + "," + matrix.f + ")";

	element.setAttribute("transform", s);
}

/**
 * Dumps a matrix to a string (useful for debug).
 */
function dumpMatrix(matrix) {
	var s = "[ " + matrix.a + ", " + matrix.c + ", " + matrix.e + "\n  " + matrix.b + ", " + matrix.d + ", " + matrix.f + "\n  0, 0, 1 ]";

	return s;
}

/**
 * Sets attributes of an element.
 */
function setAttributes(element, attributes){
	for (i in attributes)
		element.setAttributeNS(null, i, attributes[i]);
}

/**
 * Handle mouse move event.
 */
function handleMouseWheel(evt) {
	if(evt.preventDefault)
		evt.preventDefault();

	evt.returnValue = false;

	var svgDoc = evt.target.ownerDocument;

	var delta;

	if(evt.wheelDelta)
		delta = evt.wheelDelta / 3600; // Chrome/Safari
	else
		delta = evt.detail / -90; // Mozilla

	var z = 1 + delta; // Zoom factor: 0.9/1.1

	var g = svgDoc.getElementById("viewport");

	var p = getEventPoint(evt);

	p = p.matrixTransform(g.getCTM().inverse());

	// Compute new scale matrix in current mouse position
	var k = root.createSVGMatrix().translate(p.x, p.y).scale(z).translate(-p.x, -p.y);

        setCTM(g, g.getCTM().multiply(k));

	stateTf = stateTf.multiply(k.inverse());
}

/**
 * Handle mouse move event.
 */
function handleMouseMove(evt) {
	if(evt.preventDefault)
		evt.preventDefault();

	evt.returnValue = false;

	var svgDoc = evt.target.ownerDocument;

	var g = svgDoc.getElementById("viewport");

	if(state == 'pan') {
		// Pan mode
		var p = getEventPoint(evt).matrixTransform(stateTf);

		setCTM(g, stateTf.inverse().translate(p.x - stateOrigin.x, p.y - stateOrigin.y));
	} else if(state == 'move') {
		// Move mode
		var p = getEventPoint(evt).matrixTransform(g.getCTM().inverse());

		setCTM(stateTarget, root.createSVGMatrix().translate(p.x - stateOrigin.x, p.y - stateOrigin.y).multiply(g.getCTM().inverse()).multiply(stateTarget.getCTM()));

		stateOrigin = p;
	}
}

/**
 * Handle click event.
 */
function handleMouseDown(evt) {
	if(evt.preventDefault)
		evt.preventDefault();

	evt.returnValue = false;

	var svgDoc = evt.target.ownerDocument;

	var g = svgDoc.getElementById("viewport");

	if(true || evt.target.tagName == "svg") {
		// Pan mode
		state = 'pan';

		stateTf = g.getCTM().inverse();

		stateOrigin = getEventPoint(evt).matrixTransform(stateTf);
	} else {
		// Move mode
		state = 'move';

		stateTarget = evt.target;

		stateTf = g.getCTM().inverse();

		stateOrigin = getEventPoint(evt).matrixTransform(stateTf);
	}
}

/**
 * Handle mouse button release event.
 */
function handleMouseUp(evt) {
	if(evt.preventDefault)
		evt.preventDefault();

	evt.returnValue = false;

	var svgDoc = evt.target.ownerDocument;

	if(state == 'pan' || state == 'move') {
		// Quit pan mode
		state = '';
	}
}
]]></script>
'''

def rewrite_svg(svgfile, opt_svg=False):
    with open(svgfile, 'r') as f:
        svg = f.read()
    
    # Remove the original file since we'll rewrite it
    os.unlink(svgfile)

    # 1. 移除原 viewBox，设置 width/height 为 100%
    svg = re.sub(
        r'<svg([^>]*)width="[^"]*"([^>]*)height="[^"]*"([^>]*)viewBox="[^"]*"',
        r'<svg\1width="100%"\2height="100%"\3',
        svg
    )

    # 2. 在 <svg> 标签后插入 JavaScript
    svg = re.sub(
        r'(<svg[^>]*>)',
        r'\1' + SVGPAN,
        svg
    )

    # 3. 包裹所有内容到 <g id="viewport"> 中
    # 找到第一个 <g> 之前和 </svg> 之前的位置
    svg = re.sub(
        r'(<svg[^>]*>.*?)(<g[^>]*>)',
        r'\1<g id="viewport" transform="translate(0,0)">\2',
        svg,
        flags=re.DOTALL
    )

    # 4. 在结束前添加 </g>
    svg = re.sub(
        r'(.*)(</svg>)',
        r'\1</g>\2',
        svg,
        flags=re.DOTALL
    )

    # Write back to temporary file
    with open(svgfile, 'w') as f:
        f.write(svg)

def svg_javascript():
    """返回 SVG 交互式缩放/平移所需的 JavaScript 代码"""
    return """
    <script type="text/javascript"><![CDATA[
    // 简单的缩放和平移交互
    (function() {
        var svg = document.querySelector('svg');
        var viewport = document.getElementById('viewport');
        var isPanning = false;
        var startPoint = { x: 0, y: 0 };
        var endPoint = { x: 0, y: 0 };
        var scale = 1;
        
        svg.addEventListener('mousedown', function(e) {
            isPanning = true;
            startPoint = { x: e.clientX, y: e.clientY };
        });
        
        svg.addEventListener('mousemove', function(e) {
            if (!isPanning) return;
            endPoint = { x: e.clientX, y: e.clientY };
            var dx = (endPoint.x - startPoint.x) / scale;
            var dy = (endPoint.y - startPoint.y) / scale;
            var transform = viewport.getAttribute('transform');
            var translate = transform.match(/translate\(([^)]+)\)/);
            if (translate) {
                var xy = translate[1].split(',').map(parseFloat);
                viewport.setAttribute('transform', 
                    `translate(${xy[0] + dx},${xy[1] + dy}) scale(${scale})`);
            }
            startPoint = endPoint;
        });
        
        svg.addEventListener('mouseup', function() {
            isPanning = false;
        });
        
        svg.addEventListener('wheel', function(e) {
            e.preventDefault();
            var delta = e.deltaY > 0 ? 0.9 : 1.1;
            scale *= delta;
            
            var transform = viewport.getAttribute('transform');
            var translate = transform.match(/translate\(([^)]+)\)/);
            if (translate) {
                viewport.setAttribute('transform', 
                    `${translate[0]} scale(${scale})`);
            }
        });
    })();
    ]]></script>
    """

def rewrite_svg2(svgfile, opt_svg=False):
    try:
        with open(svgfile, 'r') as f:
            svg = f.read()
        
        # 调试：打印原始SVG的前200个字符
        print("Original SVG start:", svg[:200])
        
        # 1. 修改width/height为100%，移除viewBox
        svg = re.sub(
            r'<svg\s+([^>]*)width="[^"]*"\s*([^>]*)height="[^"]*"\s*([^>]*)viewBox="[^"]*"\s*([^>]*)>',
            r'<svg \1\2\3width="100%" height="100%" \4>',
            svg,
            flags=re.IGNORECASE
        )
        
        # 2. 在svg开始标签后插入JavaScript
        svg = re.sub(
            r'(<svg[^>]*>)',
            r'\1' + svg_javascript(),
            svg
        )
        
        # 3. 找到第一个<g>标签，在前面添加viewport组
        svg = re.sub(
            r'(<svg[^>]*>.*?)(<g[^>]*>)',
            r'\1<g id="viewport" transform="translate(0,0) scale(1)">\2',
            svg,
            flags=re.DOTALL
        )
        
        # 4. 在结束前添加</g>
        svg = re.sub(
            r'(.*)(</svg>)',
            r'\1</g>\2',
            svg,
            flags=re.DOTALL
        )
        
        # 调试：打印修改后的SVG前300个字符
        print("Modified SVG start:", svg[:300])
        
        if opt_svg:
            print(svg)
        else:
            # 写回文件
            with open(svgfile, 'w') as f:
                f.write(svg)
                
    except Exception as e:
        print(f"Error processing SVG: {str(e)}")
        raise
