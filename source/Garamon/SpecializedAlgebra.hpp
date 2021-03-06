/* Copyright(C) ga-developers
 *
 * Repository: https://github.com/ga-developers/ga-benchmark.git
 * 
 * This file is part of the GA-Benchmark project.
 * 
 * GA-Benchmark is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * GA-Benchmark is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with GA-Benchmark. If not, see <https://www.gnu.org/licenses/>.
 */

#ifndef __GABM_SPECIALIZED_ALGEBRA_HPP__
#define __GABM_SPECIALIZED_ALGEBRA_HPP__

#if GABM_CHECK_MODEL(ConformalModel)

    #if GABM_D_DIMENSIONS == 2
        
        #include <c2ga/Mvec.hpp>
        using namespace c2ga;

        static auto const e1 = c2ga::e1<gabm::real_t>();
        static auto const e2 = c2ga::e2<gabm::real_t>();
        static auto const no = c2ga::eo<gabm::real_t>();
        static auto const ni = c2ga::ei<gabm::real_t>();

        template<typename Type>
        inline Mvec<Type> euclidean_vector(Type const &x, Type const &y) {
            Mvec<Type> mv;
            mv[E1] = x;
            mv[E2] = y;
            return mv;
        }

        template<typename Type>
        inline Mvec<Type> point(Type const &x, Type const &y) {
            Mvec<Type> mv;
            mv[E1] = x;
            mv[E2] = y;
            mv[Ei] = 0.5 * mv.quadraticNorm();
            mv[Eo] = 1.0;
            return mv;
        }

    #elif GABM_D_DIMENSIONS == 3
        
        #include <c3ga/Mvec.hpp>
        using namespace c3ga;

        static auto const e1 = c3ga::e1<gabm::real_t>();
        static auto const e2 = c3ga::e2<gabm::real_t>();
        static auto const e3 = c3ga::e3<gabm::real_t>();
        static auto const no = c3ga::eo<gabm::real_t>();
        static auto const ni = c3ga::ei<gabm::real_t>();

        template<typename Type>
        inline Mvec<Type> euclidean_vector(Type const &x, Type const &y, Type const &z) {
            Mvec<Type> mv;
            mv[E1] = x;
            mv[E2] = y;
            mv[E3] = z;
            return mv;
        }

        template<typename Type>
        inline Mvec<Type> point(Type const &x, Type const &y, Type const &z) {
            Mvec<Type> mv;
            mv[E1] = x;
            mv[E2] = y;
            mv[E3] = z;
            mv[Ei] = 0.5 * mv.quadraticNorm();
            mv[Eo] = 1.0;
            return mv;
        }

    #endif

#elif GABM_CHECK_MODEL(EuclideanModel)

    #if GABM_D_DIMENSIONS == 2
        
        #include <e2ga/Mvec.hpp>
        using namespace e2ga;

    #elif GABM_D_DIMENSIONS == 3
        
        #include <e3ga/Mvec.hpp>
        using namespace e3ga;

    #elif GABM_D_DIMENSIONS == 4
        
        #include <e4ga/Mvec.hpp>
        using namespace e4ga;

    #elif GABM_D_DIMENSIONS == 5
        
        #include <e5ga/Mvec.hpp>
        using namespace e5ga;

    #endif

#elif GABM_CHECK_MODEL(HomogeneousModel)

    #if GABM_D_DIMENSIONS == 2
        
        #include <h2ga/Mvec.hpp>
        using namespace h2ga;

    #elif GABM_D_DIMENSIONS == 3
        
        #include <h3ga/Mvec.hpp>
        using namespace h3ga;

    #elif GABM_D_DIMENSIONS == 4
        
        #include <h4ga/Mvec.hpp>
        using namespace h4ga;

    #endif

#elif GABM_CHECK_MODEL(MinkowskiModel)

    #if GABM_D_DIMENSIONS == 2
        
        #include <m2ga/Mvec.hpp>
        using namespace m2ga;

    #elif GABM_D_DIMENSIONS == 3
        
        #include <m3ga/Mvec.hpp>
        using namespace m3ga;

    #endif

#endif

template<typename RotorType, typename ArgumentType>
inline decltype(auto) apply_rotor(RotorType const &rotor, ArgumentType const &arg) {
    return rotor * arg * ~rotor;
}

#endif // __GABM_SPECIALIZED_ALGEBRA_HPP__
