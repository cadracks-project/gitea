// Copyright 2014 The Gogs Authors. All rights reserved.
// Use of this source code is governed by a MIT-style
// license that can be found in the LICENSE file.

package routers

import (
	"code.gitea.io/gitea/modules/base"
	"code.gitea.io/gitea/modules/context"
)

const (
	tplPartners base.TplName = "partners"
)

func Partners(ctx *context.Context){
	ctx.HTML(200, tplPartners)
}
