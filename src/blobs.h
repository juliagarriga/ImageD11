
/*
# ImageD11_v1.0 Software for beamline ID11
# Copyright (C) 2005-2007  Jon Wright
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
*/

#ifndef _blobs_h
#define _blobs_h

#ifdef _MSC_VER
typedef __int8 int8_t;
typedef (unsigned __int16) uint16_t;
typedef __int32 int32_t;
#else
#include <stdint.h>
#endif

/* If we define functions as local they can be inlined at link time
 * in a shared library (e.g. not shared and overridden by LD_PRELOAD)
 */

#ifdef __GNUC__
 #if __GNUC__ >= 4
   #define DLL_PUBLIC __attribute__ ((visibility ("default")))
   #define DLL_LOCAL  __attribute__ ((visibility ("hidden")))
 #else
   #define DLL_PUBLIC
   #define DLL_LOCAL 
 #endif
#else
   #define DLL_PUBLIC
   #define DLL_LOCAL 
#endif

DLL_LOCAL
void match(int32_t * new, int32_t * old, int32_t * S);

DLL_LOCAL
int32_t *dset_initialise(int32_t size);	/* array to hold real values of each */

DLL_LOCAL
int32_t *dset_new(int32_t ** S, int32_t * v);

DLL_LOCAL
void dset_makeunion(int32_t * S, int32_t r1, int32_t r2);

DLL_LOCAL
void dset_link(int32_t * S, int32_t r1, int32_t r2);

DLL_LOCAL
int32_t dset_find(int32_t x, int32_t * S);

DLL_LOCAL
int32_t *dset_compress(int32_t ** pS, int32_t * np);

DLL_PUBLIC
  /* Spot_ID - to be generated when writing out */
enum {
    s_1 = 0,			/* 1 Npix */
    s_I,			/* 2 Sum intensity */
    s_I2,			/* 3 Sum intensity^2 */
    s_fI,			/* 4 Sum f * intensity */
    s_ffI,			/* 5 Sum f * f* intensity */
    s_sI,			/* 6 Sum s * intensity */
    s_ssI,			/* 7 Sum s * s * intensity */
    s_sfI,			/* 8 Sum f * s * intensity */
    s_oI,			/* 9 sum omega * intensity */
    s_ooI,			/* 10 sum omega2 * intensity */
    s_soI,			/* 11 sum omega * s * intensity */
    s_foI,			/* 12 sum omega * f * intensity */

    mx_I,			/* 13 Max intensity */
    mx_I_f,			/* 14 fast at Max intensity */
    mx_I_s,			/* 15 slow at Max intensity */
    mx_I_o,			/* 16 omega at max I */

    bb_mx_f,			/* 17 max of f */
    bb_mx_s,			/* 18 max of s */
    bb_mx_o,			/* 19 max of omega */
    bb_mn_f,			/* 20 min of f */
    bb_mn_s,			/* 21 min of s */
    bb_mn_o,			/* 22 min of o */

    avg_i,			/* Average intensity */
    f_raw,			/* fast centre of mass */
    s_raw,			/* slow centre of mass */
    o_raw,			/* omega centre of mass */
    m_ss,			/* moments */
    m_ff,
    m_oo,
    m_sf,
    m_so,
    m_fo,

    f_cen,			/* Filled in elsewhere  - spatial correction */
    s_cen,			/* ditto */

    dety,			/*Filled in elsewhere  - flip to HFPO book */
    detz,			/*Filled in elsewhere  - flip to HFPO book */

    NPROPERTY			/* Number of properties if starting at 0 */
};

/*void new_blob(double blob[], int i, int j, double val);*/

DLL_LOCAL
void add_pixel(double blob[], int i, int j, double val, double omega);

DLL_LOCAL
void merge(double blob1[], double blob2[]);

DLL_LOCAL
void compute_moments(double blobs[], int nblobs);

#endif				/* _blobs_h */
